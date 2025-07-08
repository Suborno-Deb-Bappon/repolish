#!/usr/bin/env python
import gradio as gr
import os
import json
import markdown
import re
from repolish.crew import ReadmeGeneratorCrew

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

def clean_readme_content(content):
    """Remove unwanted code block markers from README content"""
    # Remove starting ```markdown and ending ```
    content = re.sub(r'^\s*```(markdown)?\s*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\s*```\s*$', '', content, flags=re.IGNORECASE)
    
    # Remove any remaining triple backticks that wrap the entire content
    content = content.strip()
    if content.startswith('```') and content.endswith('```'):
        content = content[3:-3].strip()
    
    # Remove any language specifier if present
    if content.startswith('markdown'):
        content = content[len('markdown'):].strip()
    
    return content


def run_crew(repo_url, create_pr=False):
    """
    Run the README generator crew and return the generated README content and PR status.
    """
    try:
        inputs = {
            'repo_url': repo_url,
            'output_file': 'output/README.md',
        }

        # Create and run the crew
        crew_instance = ReadmeGeneratorCrew()
        result = crew_instance.crew().kickoff(inputs=inputs)
        
        # Clean the README content
        readme_content = clean_readme_content(str(result))
        
        # Save the README content to file
        output_file = inputs['output_file']
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)
        except Exception as file_error:
            print(f"Warning: Could not save to file: {file_error}")
        
        # Handle PR creation separately
        pr_status_html = "<div class='pr-status-box'>No pull request created.</div>"
        if create_pr:
            try:
                pr_result = crew_instance.create_pr(repo_url, readme_content)
                
                if isinstance(pr_result, dict) and pr_result.get('success') is True and 'pr_url' in pr_result:
                    pr_url = pr_result['pr_url']
                    pr_status = f"✅ Successfully created pull request: <a href='{pr_url}' target='_blank'>{pr_url}</a>"
                    pr_status_html = f"<div class='pr-status-box success-status'>{pr_status}</div>"
                else:
                    error_msg = str(pr_result)
                    pr_status = f"❌ PR creation failed: {error_msg}"
                    pr_status_html = f"<div class='pr-status-box error-status'>{pr_status}</div>"

                
            except Exception as pr_error:
                pr_status = f"❌ PR creation error: {str(pr_error)}"
                pr_status_html = f"<div class='pr-status-box error-status'>{pr_status}</div>"
        
        # Return both raw and HTML versions of the README
        readme_html = markdown.markdown(readme_content)
        return readme_content, readme_html, pr_status_html
    
    except Exception as e:
        error_message = f"❌ Error: {str(e)}"
        print(f"Full error details: {e}")
        error_html = f"<div class='pr-status-box error-status'>{error_message}</div>"
        return error_message, error_message, error_html

def run():
    """
    Entry point for crewai run command.
    """
    print("README Generator Crew")
    print("This crew generates README files for GitHub repositories.")
    
    # Example usage
    repo_url = input("Enter GitHub repository URL: ")
    create_pr_input = input("Create pull request? (y/n): ").lower()
    create_pr = create_pr_input == 'y'
    
    readme_content, _, pr_status = run_crew(repo_url, create_pr)
    
    print("\n" + "="*50)
    print("GENERATED README:")
    print("="*50)
    print(readme_content)
    print("\n" + "="*50)
    print("PR STATUS:", pr_status)
    print("="*50)

def launch_gradio_interface():
    """
    Create and launch the Gradio interface with enhanced output display.
    """
    with gr.Blocks(title="RepoLish", theme="soft") as demo:
        gr.Markdown("# 🚀 RepoLish")
        gr.Markdown("Enter a GitHub repository URL to generate a professional README.md file")
        
        with gr.Row():
            repo_url_input = gr.Textbox(
                label="GitHub Repository URL", 
                placeholder="https://github.com/owner/repo",
                value="https://github.com/Suborno-Deb-Bappon/Q-A-Chatbot",
                scale=4
            )
            create_pr_checkbox = gr.Checkbox(
                label="Create Pull Request (requires write access to repo)",
                scale=1
            )
        
        generate_button = gr.Button("Generate README", variant="primary", size="lg")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📝 Generated README Preview")
                readme_preview = gr.HTML(
                    label="Rendered Preview",
                    value="<div style='padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px; background: #f8f9fa;'>Your generated README will appear here...</div>"
                )
                
                gr.Markdown("### 📋 Raw Markdown Content")
                readme_raw = gr.Code(
                    label="Markdown Code",
                    language="markdown",
                    interactive=True,
                    lines=20,
                    value="",
                    elem_classes="markdown-editor"
                )
                
            with gr.Column():
                gr.Markdown("### ℹ️ Status Information")
                pr_status_output = gr.HTML(
                    label="Pull Request Status",
                    value="<div class='pr-status-box'>Status will appear here...</div>"
                )
                
                gr.Markdown("### 💾 Output File")
                output_file = gr.File(
                    label="Download README.md",
                    value="output/README.md",
                    visible=True
                )
        
        # Custom CSS for better Markdown rendering
        demo.css = """
        .markdown-editor {
            font-family: monospace;
            font-size: 14px;
        }
        .markdown-editor .cm-content {
            padding: 10px;
        }
        .pr-status-box {
            padding: 12px;
            border-radius: 6px;
            background-color: #f8f9fa;
            border: 1px solid #e0e0e0;
            margin-top: 10px;
            font-size: 14px;
        }
        .success-status {
            color: #2e7d32;
            background-color: #e8f5e9;
            border-color: #c8e6c9;
        }
        .error-status {
            color: #c62828;
            background-color: #ffebee;
            border-color: #ffcdd2;
        }
        .status-header {
            font-weight: bold;
            margin-bottom: 5px;
            color: #333;
        }
        a {
            color: #1976d2;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        """
        
        # Update outputs when button is clicked
        generate_button.click(
            fn=run_crew,
            inputs=[repo_url_input, create_pr_checkbox],
            outputs=[readme_raw, readme_preview, pr_status_output]
        )
        
        # Update file download when raw content updates
        readme_raw.change(
            fn=lambda x: gr.File(value="output/README.md"),
            inputs=[readme_raw],
            outputs=[output_file]
        )
    
    demo.launch(server_name="127.0.0.1", server_port=7860)

if __name__ == "__main__":
    launch_gradio_interface()