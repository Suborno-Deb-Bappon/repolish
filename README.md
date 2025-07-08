# Repolish

# 🛠️ Repolish

**Repolish** is an AI-powered tool that automatically generates, improves, and formats README files for GitHub repositories. Built on a CrewAI-based agentic architecture, Repolish understands your project, constructs a professional README, and can even submit it as a pull request — all through a clean, intuitive Gradio interface.

---

## 🚀 Features

- **Automated README Generation**  
  Analyzes your repository to produce clear, concise, and well-structured documentation.

- **Agentic AI Architecture**  
  Powered by [CrewAI](https://github.com/joaomdmoura/crewAI), Repolish leverages multiple intelligent agents, each handling a specific task like summarization, formatting, or structure design.

- **Markdown Cleanup**  
  Cleans up messy or redundant markdown to ensure a professional finish.

- **Pull Request Integration**  
  Optionally creates a pull request to your repository with the improved README file.

- **Gradio UI**  
  Simple web-based interface — no need to run anything from the command line (unless you want to).

---

## 📦 Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-username/repolish.git
cd repolish
pip install -r requirements.txt
```

## 🧑‍💻 Usage
Start the app using:
```bash
python -m repolish.main
```
This will launch a Gradio interface where you can:

  - Enter a GitHub repository URL.
  - Click "Generate" to let Repolish analyze and build a professional README.
  - Optionally, allow it to create a pull request to the source repository.

## 🗂️ Project Structure
repolish/
├── config/
│   ├── agents.yaml       # CrewAI agent definitions
│   └── tasks.yaml        # Task definitions
├── tools/                # Custom tools for agents
├── crew.py               # CrewAI crew setup
├── main.py               # App entry point (Gradio UI)
└── ...
