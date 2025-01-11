from flask import Flask, request, render_template_string
from text_pipeline import process_subtitle_text, get_first_definition

app = Flask(__name__)

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Subtitle Uploader</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h1>Upload Subtitles</h1>
    <form action="/upload" method="POST" enctype="multipart/form-data">
        <label for="subtitle_file">Choose a subtitle file (e.g., .srt or .txt)</label><br>
        <input type="file" name="subtitle_file" accept=".srt,.txt" required><br><br>
        
        <label for="top_n">How many top words?</label><br>
        <input type="number" name="top_n" value="20" style="width: 60px;"><br><br>
        
        <input type="submit" value="Process" style="padding: 6px 12px;">
    </form>
</body>
</html>
"""

RESULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Results for Top {{ top_n }} Words</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        table {
            border-collapse: collapse;
            margin-top: 20px;
            width: 90%%;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px 12px;
        }
        th {
            background-color: #f2f2f2;
        }
        .definition-short {
            font-style: italic;
            color: #555;
        }
        .toggle-btn {
            cursor: pointer;
            color: blue;
            text-decoration: underline;
            background: none;
            border: none;
            padding: 0;
        }
        .hidden {
            display: none;
        }
        .definition-details {
            margin-left: 20px;
            margin-top: 10px;
            color: #333;
        }
        .definition-details p {
            margin-bottom: 5px;
        }
    </style>
</head>
<body>
    <h1>Top {{ top_n }} Words from Subtitles</h1>
    <p>Here are the most frequent words, along with a short definition snippet (if found).</p>
    
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Word</th>
                <th>Frequency</th>
                <th>Definition Snippet</th>
                <th>More</th>
            </tr>
        </thead>
        <tbody>
            {% for item in results %}
            <tr>
                <td>{{ loop.index }}</td>
                <td style="font-weight: bold;">{{ item.word }}</td>
                <td>{{ item.frequency }}</td>
                <td>
                    {% set short_definition = get_first_definition(item.definition_data) %}
                    {% if short_definition %}
                        <span class="definition-short">{{ short_definition }}</span>
                    {% else %}
                        <span style="color: #999;">No short definition found</span>
                    {% endif %}
                </td>
                <td>
                    {% if item.definition_data and item.definition_data|length > 0 %}
                        <button class="toggle-btn" onclick="toggleDetails('{{ loop.index0 }}', this)">
                            Show More
                        </button>
                        
                        <div id="details-{{ loop.index0 }}" class="hidden definition-details">
                            {% for entry in item.definition_data %}
                                <p><strong>Word:</strong> {{ entry.word|default('Unknown') }}</p>
                                {% for meaning in entry.meanings or [] %}
                                    <p>
                                    <strong>Part of Speech:</strong> {{ meaning.partOfSpeech or 'Unknown' }}<br>
                                    {% for defn in meaning.definitions or [] %}
                                        <strong>Definition:</strong> {{ defn.definition }}<br>
                                        {% if defn.example %}
                                        <strong>Example:</strong> {{ defn.example }}<br>
                                        {% endif %}
                                    {% endfor %}
                                    </p>
                                    <hr>
                                {% endfor %}
                            {% endfor %}
                        </div>
                    {% else %}
                        <span style="color: #999;">No definitions found</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <p style="margin-top: 30px;">
        <a href="/">Go back</a>
    </p>
    
    <script>
        function toggleDetails(idx, btn) {
            let detailsDiv = document.getElementById('details-' + idx);
            if (detailsDiv.classList.contains('hidden')) {
                detailsDiv.classList.remove('hidden');
                btn.textContent = 'Show Less';
            } else {
                detailsDiv.classList.add('hidden');
                btn.textContent = 'Show More';
            }
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    """Renders the main upload form."""
    return render_template_string(INDEX_TEMPLATE)

@app.route("/upload", methods=["POST"])
def upload():
    """Handles the file upload and returns the top words result."""
    file = request.files.get("subtitle_file")
    if not file:
        return "No file provided", 400

    top_n = request.form.get("top_n", "20")
    try:
        top_n = int(top_n)
    except ValueError:
        top_n = 20
    
    raw_text = file.read().decode("utf-8", errors="replace")
    
    # Use our pipeline function
    results = process_subtitle_text(raw_text, top_n=top_n)
    
    return render_template_string(
        RESULT_TEMPLATE,
        top_n=top_n,
        results=results,
        get_first_definition=get_first_definition
    )

if __name__ == "__main__":
    app.run(debug=True)

