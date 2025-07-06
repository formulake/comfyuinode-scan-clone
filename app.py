import os
import re
import subprocess
import time
import configparser
from pathlib import Path
import gradio as gr

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib


def extract_github_url_from_pyproject(pyproject_path):
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})
        urls = project.get("urls", {})
        if isinstance(urls, dict):
            for _, url in urls.items():
                if isinstance(url, str) and "github.com" in url:
                    return url.strip().removesuffix(".git")

        poetry = data.get("tool", {}).get("poetry", {})
        url = poetry.get("repository")
        if isinstance(url, str) and "github.com" in url:
            return url.strip().removesuffix(".git")
    except Exception:
        pass
    return None


def extract_github_urls(custom_nodes_path, output_format, include_names):
    base_path = Path(custom_nodes_path)
    if not base_path.exists():
        return "❌ Directory not found.", None

    repos = []
    for subdir in base_path.iterdir():
        if not subdir.is_dir():
            continue

        url = None
        git_config_path = subdir / ".git" / "config"
        if git_config_path.exists():
            config = configparser.ConfigParser()
            config.read(git_config_path)
            try:
                url = config['remote "origin"']['url']
                if url.startswith("git@github.com:"):
                    url = url.replace("git@github.com:", "https://github.com/").replace(".git", "")
                elif url.endswith(".git"):
                    url = url[:-4]
            except KeyError:
                pass

        if url is None:
            pyproject_path = subdir / "pyproject.toml"
            if pyproject_path.exists():
                url = extract_github_url_from_pyproject(pyproject_path)

        if url:
            repos.append((subdir.name, url))

    if not repos:
        return "⚠️ No valid GitHub URLs found.", None

    lines = []
    for name, url in repos:
        line = f"{name}: {url}" if include_names else url
        if output_format == "md":
            line = f"- **{name}**: [{url}]({url})" if include_names else f"- [{url}]({url})"
        lines.append(line)

    output_content = "\n".join(lines)
    filename = "github_urls_with_names." + output_format if include_names else "github_urls." + output_format
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output_content)

    return output_content, filename


def parse_urls_from_file(file_path):
    urls = []
    url_pattern = r"https?://github\.com/[^\s\]\)]+"
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(url_pattern, line)
            if match:
                url = match.group(0).strip().removesuffix(".git")
                if url not in urls:
                    urls.append(url)
    return urls


def clone_all_repos(uploaded_file, target_dir):
    target_path = Path(target_dir)
    if not target_path.exists():
        try:
            target_path.mkdir(parents=True)
        except Exception as e:
            yield f"❌ Failed to create target directory: {e}"
            return

    urls = parse_urls_from_file(uploaded_file.name)
    total = len(urls)
    if total == 0:
        yield "⚠️ No valid GitHub URLs found in the file."
        return

    yield f"🔄 Starting clone of {total} repositories...\n"

    for i, url in enumerate(urls):
        folder_name = url.rstrip("/").split("/")[-1]
        destination = target_path / folder_name

        yield f"🔹 Cloning {folder_name} ({i+1} of {total})..."

        if destination.exists():
            yield f"⏭️ Skipped (already exists): {folder_name}\n"
            continue

        try:
            result = subprocess.run(
                ["git", "clone", url, str(destination)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                yield f"✅ Cloned: {folder_name}\n"
            else:
                yield f"❌ Failed: {folder_name} → {result.stderr.strip()}\n"
        except Exception as e:
            yield f"❌ Exception cloning {folder_name}: {e}\n"

    yield f"\n✅ Done cloning."


def load_repo_list(file_obj):
    filepath = file_obj.name if hasattr(file_obj, "name") else file_obj
    urls = parse_urls_from_file(filepath)
    repo_map = {url.rstrip("/").split("/")[-1]: url for url in urls}
    repo_names = list(repo_map.keys())
    return gr.update(choices=repo_names, value=[]), repo_map, repo_names


def select_all_checked(choices):
    return gr.update(value=choices)


def clone_selected_repos(selected_names, repo_map, target_dir):
    if not selected_names:
        yield "⚠️ No repositories selected."
        return

    total = len(selected_names)
    target_path = Path(target_dir)
    if not target_path.exists():
        try:
            target_path.mkdir(parents=True)
        except Exception as e:
            yield f"❌ Failed to create target directory: {e}"
            return

    yield f"🔄 Cloning {total} selected repositories...\n"

    for i, name in enumerate(selected_names):
        url = repo_map.get(name)
        destination = target_path / name

        yield f"🔹 Cloning {name} ({i+1} of {total})..."

        if destination.exists():
            yield f"⏭️ Skipped (already exists): {name}\n"
            continue

        try:
            result = subprocess.run(
                ["git", "clone", url, str(destination)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                yield f"✅ Cloned: {name}\n"
            else:
                yield f"❌ Failed: {name} → {result.stderr.strip()}\n"
        except Exception as e:
            yield f"❌ Exception cloning {name}: {e}\n"

    yield f"\n✅ Done cloning selected repos."


# 🧠 Gradio UI
with gr.Blocks(title="Comfy Node Scan and Clone") as demo:
    gr.Markdown("## 🧠 Comfy Node Scan and Clone")

    with gr.Tab("Node Scanner"):
        with gr.Row():
            folder_input = gr.Textbox(label="Path to custom_nodes directory")
            output_format = gr.Radio(["txt", "md"], label="Output format", value="txt")
            include_names = gr.Checkbox(label="Include repo folder names", value=True)
        scan_button = gr.Button("Scan and Export")
        output_text = gr.Textbox(label="Exported GitHub URLs", lines=20)
        download_file = gr.File(label="Download Export")
        scan_button.click(extract_github_urls, [folder_input, output_format, include_names], [output_text, download_file])

    with gr.Tab("Simple Cloner"):
        upload_file = gr.File(label="Upload GitHub URL list")
        clone_path = gr.Textbox(label="Target custom_nodes path")
        clone_btn = gr.Button("Clone All Repos")
        clone_log = gr.TextArea(label="Clone Log", lines=25, interactive=False)
        clone_btn.click(clone_all_repos, [upload_file, clone_path], clone_log)

    with gr.Tab("Advanced Cloner"):
        adv_upload = gr.File(label="Upload GitHub URL list")
        repo_checkboxes = gr.CheckboxGroup(label="Select Repositories to Clone")
        map_state = gr.State()
        choices_state = gr.State()
        load_button = gr.Button("Load Repo List")
        target_path_adv = gr.Textbox(label="Target custom_nodes path")
        select_all = gr.Button("Select All")
        clone_selected = gr.Button("Clone Selected")
        output_selected = gr.TextArea(label="Clone Log", lines=25, interactive=False)

        load_button.click(load_repo_list, [adv_upload], [repo_checkboxes, map_state, choices_state])
        select_all.click(fn=select_all_checked, inputs=[choices_state], outputs=repo_checkboxes)
        clone_selected.click(clone_selected_repos, [repo_checkboxes, map_state, target_path_adv], [output_selected])

demo.launch()
