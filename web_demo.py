from pathlib import Path

from flask import Flask, jsonify, render_template, request

from content_pipeline import AUDIO_FILE_TYPES, get_example_files
from conversation_agent import ConversationContentAgent
from validation import build_validation_checks


BASE_DIR = Path(__file__).parent
TEXT_FILE_TYPES = {"txt", "md"}

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "web_demo" / "templates"),
    static_folder=str(BASE_DIR / "web_demo" / "static"),
)
_agent: ConversationContentAgent | None = None


def get_agent() -> ConversationContentAgent:
    global _agent
    if _agent is None:
        _agent = ConversationContentAgent()
    return _agent


def get_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def output_to_payload(output) -> dict:
    return {
        "source_description": output.source_description,
        "source_text": output.source_text,
        "facts": output.facts,
        "markdown": output.markdown,
        "outputs": {
            key: {
                "text": result["text"],
                "validation": build_validation_checks(key, result["text"]),
            }
            for key, result in output.results.items()
        },
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/examples")
def examples():
    example_payload = []
    for example_path in get_example_files():
        example_payload.append(
            {
                "filename": example_path.name,
                "label": example_path.stem.replace("_", " ").capitalize(),
                "content": example_path.read_text(encoding="utf-8"),
            }
        )
    return jsonify({"examples": example_payload})


@app.post("/api/generate")
def generate():
    try:
        source_text = request.form.get("source_text", "").strip()
        uploaded_file = request.files.get("source_file")
        agent = get_agent()

        if uploaded_file and uploaded_file.filename:
            filename = uploaded_file.filename
            file_content = uploaded_file.read()
            extension = get_extension(filename)

            if extension in TEXT_FILE_TYPES:
                output = agent.process_text_file(filename, file_content)
            elif extension in AUDIO_FILE_TYPES:
                output = agent.process_audio_file(filename, file_content)
            else:
                return (
                    jsonify(
                        {
                            "error": (
                                "Formato nao suportado. Usa texto, .txt, .md "
                                "ou um ficheiro de audio."
                            )
                        }
                    ),
                    400,
                )
        elif source_text:
            output = agent.process_text(source_text, "texto escrito no painel web")
        else:
            return jsonify({"error": "Insere texto ou carrega um ficheiro."}), 400

        return jsonify(output_to_payload(output))
    except Exception as error:
        return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    app.run(debug=True)
