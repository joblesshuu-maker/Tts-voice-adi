from flask import Flask, request, render_template_string, send_file, jsonify
import os
import uuid
import threading

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global job storage
jobs = {}
processes = {}  # Track running processes for stop functionality

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Tortoise TTS OpenUI</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
<div class="container mx-auto max-w-6xl py-8">
    <h1 class="text-3xl font-bold mb-6 text-center">Tortoise TTS OpenUI</h1>
    <form id="tts-form" method="post" enctype="multipart/form-data" class="bg-white p-6 rounded-lg shadow-md">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="space-y-4 col-span-1">
                <!-- Left column: text and file upload -->
                <label for="text" class="block font-semibold">Text to Synthesize:</label>
                <textarea name="text" id="text" required class="w-full border rounded p-2" rows="6">{{ request.form.text or '' }}</textarea>
                <label for="text_file" class="block font-semibold">Or upload a text file:</label>
                <input type="file" name="text_file" id="text_file" accept=".txt" class="w-full border rounded p-2">
            </div>
            <div class="space-y-4 col-span-1">
                <!-- Middle column: options -->
                <label for="voice" class="block font-semibold">Voice (comma-separated, or 'random'):</label>
                <input type="text" name="voice" id="voice" value="{{ request.form.voice or 'random' }}" class="w-full border rounded p-2">
                <label for="preset" class="block font-semibold">Preset:</label>
                <select name="preset" id="preset" class="w-full border rounded p-2">
                    <option value="ultra_fast" {% if request.form.preset == 'ultra_fast' %}selected{% endif %}>Ultra Fast</option>
                    <option value="fast" {% if request.form.preset == 'fast' or not request.form.preset %}selected{% endif %}>Fast</option>
                    <option value="standard" {% if request.form.preset == 'standard' %}selected{% endif %}>Standard</option>
                    <option value="high_quality" {% if request.form.preset == 'high_quality' %}selected{% endif %}>High Quality</option>
                </select>
                <label for="candidates" class="block font-semibold">Candidates:</label>
                <input type="number" name="candidates" id="candidates" min="1" max="10" value="{{ request.form.candidates or 1 }}" class="w-full border rounded p-2">
                <label for="seed" class="block font-semibold">Seed (optional):</label>
                <input type="number" name="seed" id="seed" value="{{ request.form.seed or '' }}" class="w-full border rounded p-2">
                <label for="device" class="block font-semibold">Device:</label>
                <select name="device" id="device" class="w-full border rounded p-2">
                    <option value="" {% if not request.form.device %}selected{% endif %}>Auto</option>
                    <option value="cuda" {% if request.form.device == 'cuda' %}selected{% endif %}>CUDA (GPU)</option>
                    <option value="cpu" {% if request.form.device == 'cpu' %}selected{% endif %}>CPU</option>
                </select>
                <label for="voices_dir" class="block font-semibold">Voices Dir (optional):</label>
                <input type="text" name="voices_dir" id="voices_dir" value="{{ request.form.voices_dir or '' }}" class="w-full border rounded p-2">
                <label for="text_split" class="block font-semibold">Text Split (e.g. 200,400):</label>
                <input type="text" name="text_split" id="text_split" value="{{ request.form.text_split or '' }}" class="w-full border rounded p-2">
                <label for="num_autoregressive_samples" class="block font-semibold">Num Autoregressive Samples:</label>
                <input type="number" name="num_autoregressive_samples" id="num_autoregressive_samples" min="1" value="{{ request.form.num_autoregressive_samples or '' }}" class="w-full border rounded p-2">
                <label for="temperature" class="block font-semibold">Temperature:</label>
                <input type="number" step="any" name="temperature" id="temperature" value="{{ request.form.temperature or '' }}" class="w-full border rounded p-2">
                <label for="length_penalty" class="block font-semibold">Length Penalty:</label>
                <input type="number" step="any" name="length_penalty" id="length_penalty" value="{{ request.form.length_penalty or '' }}" class="w-full border rounded p-2">
                <label for="repetition_penalty" class="block font-semibold">Repetition Penalty:</label>
                <input type="number" step="any" name="repetition_penalty" id="repetition_penalty" value="{{ request.form.repetition_penalty or '' }}" class="w-full border rounded p-2">
                <label for="top_p" class="block font-semibold">Top-p:</label>
                <input type="number" step="any" name="top_p" id="top_p" value="{{ request.form.top_p or '' }}" class="w-full border rounded p-2">
                <label for="max_mel_tokens" class="block font-semibold">Max Mel Tokens:</label>
                <input type="number" name="max_mel_tokens" id="max_mel_tokens" min="1" max="600" value="{{ request.form.max_mel_tokens or '' }}" class="w-full border rounded p-2">
                <label for="cvvp_amount" class="block font-semibold">CVVP Amount:</label>
                <input type="number" step="any" name="cvvp_amount" id="cvvp_amount" value="{{ request.form.cvvp_amount or '' }}" class="w-full border rounded p-2">
                <label for="diffusion_iterations" class="block font-semibold">Diffusion Iterations:</label>
                <input type="number" name="diffusion_iterations" id="diffusion_iterations" value="{{ request.form.diffusion_iterations or '' }}" class="w-full border rounded p-2">
                <label class="inline-flex items-center"><input type="checkbox" name="cond_free" {% if request.form.get('cond_free') %}checked{% endif %} class="mr-2"> Conditioning Free Diffusion</label>
                <label for="cond_free_k" class="block font-semibold">Cond Free K:</label>
                <input type="number" step="any" name="cond_free_k" id="cond_free_k" value="{{ request.form.cond_free_k or '' }}" class="w-full border rounded p-2">
                <label for="diffusion_temperature" class="block font-semibold">Diffusion Temperature:</label>
                <input type="number" step="any" name="diffusion_temperature" id="diffusion_temperature" value="{{ request.form.diffusion_temperature or '' }}" class="w-full border rounded p-2">
                <div class="flex flex-wrap gap-4 mt-4">
                    <label class="inline-flex items-center"><input type="checkbox" name="quiet" {% if request.form.get('quiet') %}checked{% endif %} class="mr-2"> Quiet</label>
                    <label class="inline-flex items-center"><input type="checkbox" name="produce_debug_state" {% if request.form.get('produce_debug_state') %}checked{% endif %} class="mr-2"> Produce Debug State</label>
                    <label class="inline-flex items-center"><input type="checkbox" name="skip_existing" {% if request.form.get('skip_existing') %}checked{% endif %} class="mr-2"> Skip Existing</label>
                    <label class="inline-flex items-center"><input type="checkbox" name="disable_redaction" {% if request.form.get('disable_redaction') %}checked{% endif %} class="mr-2"> Disable Redaction</label>
                </div>
            </div>
            <div class="flex flex-col col-span-1 space-y-4">
                <!-- Right column: progress, log, synthesize/stop buttons, result -->
                <div id="progress-section" class="mb-4 hidden">
                    <div class="w-full bg-gray-200 rounded-full h-6 mb-4 overflow-hidden relative">
                        <div id="progress-bar" class="h-6 bg-gradient-to-r from-blue-500 via-blue-400 to-blue-600 bg-[length:40px_40px] animate-stripes rounded-full absolute left-0 top-0 w-full"></div>
                    </div>
                    <div id="log-area" class="bg-black text-green-400 font-mono p-4 rounded-lg overflow-y-auto max-h-64 whitespace-pre-line shadow-inner"></div>
                </div>
                <div class="flex gap-4">
                    <button type="submit" id="synthesize-btn" class="flex-1 bg-blue-600 text-white font-bold py-2 px-4 rounded hover:bg-blue-700 transition">Synthesize</button>
                    <button type="button" id="stop-btn" class="flex-1 bg-red-600 text-white font-bold py-2 px-4 rounded hover:bg-red-700 transition hidden">Stop</button>
                </div>
                <div id="result-section" class="result bg-white p-6 rounded-lg shadow-md hidden">
                    <h2 class="text-xl font-bold mb-2">Result</h2>
                    <audio id="audio-player" controls class="w-full"></audio>
                    <p class="mt-2"><a id="download-link" href="#" download class="text-blue-600 hover:underline">Download Audio</a></p>
                </div>
            </div>
        </div>
    </form>
</div>
<script>
const form = document.getElementById('tts-form');
const progressSection = document.getElementById('progress-section');
const progressBar = document.getElementById('progress-bar');
const logArea = document.getElementById('log-area');
const resultSection = document.getElementById('result-section');
const audioPlayer = document.getElementById('audio-player');
const downloadLink = document.getElementById('download-link');
const synthesizeBtn = document.getElementById('synthesize-btn');
const stopBtn = document.getElementById('stop-btn');
let polling = false;
let currentJobId = null;

form.addEventListener('submit', function(e) {
    e.preventDefault();
    progressSection.classList.remove('hidden');
    resultSection.classList.add('hidden');
    progressBar.style.width = '100%';
    logArea.textContent = '';
    synthesizeBtn.disabled = true;
    stopBtn.classList.remove('hidden');
    const formData = new FormData(form);
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.job_id) {
            currentJobId = data.job_id;
            pollProgress(data.job_id);
        }
    });
});

stopBtn.addEventListener('click', function() {
    if (currentJobId) {
        fetch(`/stop/${currentJobId}`, { method: 'POST' })
            .then(() => {
                polling = false;
                stopBtn.classList.add('hidden');
                synthesizeBtn.disabled = false;
            });
    }
});

function pollProgress(jobId) {
    polling = true;
    function poll() {
        fetch(`/progress/${jobId}`)
            .then(res => res.json())
            .then(data => {
                logArea.textContent = data.log;
                logArea.scrollTop = logArea.scrollHeight;
                if (data.done) {
                    polling = false;
                    stopBtn.classList.add('hidden');
                    synthesizeBtn.disabled = false;
                    if (data.audio_url) {
                        audioPlayer.src = data.audio_url;
                        downloadLink.href = data.audio_url;
                        resultSection.classList.remove('hidden');
                    }
                } else if (polling) {
                    setTimeout(poll, 500);
                }
            });
    }
    poll();
}
// Add Tailwind custom animation for stripes
const style = document.createElement('style');
style.innerHTML = `
@keyframes stripes {
  0% { background-position-x: 0; }
  100% { background-position-x: 40px; }
}
.animate-stripes {
  background-image: repeating-linear-gradient(135deg,rgba(255,255,255,0.15) 0 10px,transparent 10px 20px);
  animation: stripes 1s linear infinite;
}
`;
document.head.appendChild(style);
</script>
</body>
</html>
'''

def run_tts_with_progress(cmd, env, job_id):
    import subprocess
    import re
    jobs[job_id]['progress'] = 0
    jobs[job_id]['log'] = ''
    jobs[job_id]['done'] = False
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, bufsize=1)
    processes[job_id] = process
    try:
        for line in process.stdout:
            jobs[job_id]['log'] += line
            match = re.search(r"\((\d+) of (\d+)\)", line)
            if match:
                current, total_clips = int(match.group(1)), int(match.group(2))
                progress = int(current / total_clips * 100)
                jobs[job_id]['progress'] = progress
        process.wait()
    finally:
        jobs[job_id]['progress'] = 100
        jobs[job_id]['done'] = True
        processes.pop(job_id, None)

@app.route('/stop/<job_id>', methods=['POST'])
def stop_job(job_id):
    proc = processes.get(job_id)
    if proc and proc.poll() is None:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
        except Exception:
            pass
    jobs[job_id]['done'] = True
    return jsonify({'stopped': True})

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form.get('text', '')
        # Handle uploaded text file
        if 'text_file' in request.files and request.files['text_file']:
            file = request.files['text_file']
            if file.filename:
                file_content = file.read().decode('utf-8')
                text = file_content
        if text:
            filename = f"{uuid.uuid4()}.wav"
            output_path = os.path.join(OUTPUT_FOLDER, filename)
            cmd = [
                'python', 'scripts/tortoise_tts.py',
                '-o', output_path
            ]
            # Add text
            if text:
                cmd.append(text)
            # Optional arguments
            voice = request.form.get('voice')
            if voice:
                cmd.extend(['-v', voice])
            preset = request.form.get('preset')
            if preset:
                cmd.extend(['-p', preset])
            candidates = request.form.get('candidates')
            if candidates and str(candidates) != '1':
                cmd.extend(['--candidates', str(candidates)])
            seed = request.form.get('seed')
            if seed:
                cmd.extend(['--seed', str(seed)])
            device = request.form.get('device')
            if device:
                cmd.extend(['--device', device])
            voices_dir = request.form.get('voices_dir')
            if voices_dir:
                cmd.extend(['-V', voices_dir])
            text_split = request.form.get('text_split')
            if text_split:
                cmd.extend(['--text-split', text_split])
            # Tuning options
            if request.form.get('num_autoregressive_samples'):
                cmd.extend(['--num-autoregressive-samples', str(request.form['num_autoregressive_samples'])])
            if request.form.get('temperature'):
                cmd.extend(['--temperature', str(request.form['temperature'])])
            if request.form.get('length_penalty'):
                cmd.extend(['--length-penalty', str(request.form['length_penalty'])])
            if request.form.get('repetition_penalty'):
                cmd.extend(['--repetition-penalty', str(request.form['repetition_penalty'])])
            if request.form.get('top_p'):
                cmd.extend(['--top-p', str(request.form['top_p'])])
            if request.form.get('max_mel_tokens'):
                cmd.extend(['--max-mel-tokens', str(request.form['max_mel_tokens'])])
            if request.form.get('cvvp_amount'):
                cmd.extend(['--cvvp-amount', str(request.form['cvvp_amount'])])
            if request.form.get('diffusion_iterations'):
                cmd.extend(['--diffusion-iterations', str(request.form['diffusion_iterations'])])
            if request.form.get('cond_free'):
                cmd.append('--cond-free')
            if request.form.get('cond_free_k'):
                cmd.extend(['--cond-free-k', str(request.form['cond_free_k'])])
            if request.form.get('diffusion_temperature'):
                cmd.extend(['--diffusion-temperature', str(request.form['diffusion_temperature'])])
            if request.form.get('quiet'):
                cmd.append('-q')
            if request.form.get('produce_debug_state'):
                cmd.append('--produce-debug-state')
            if request.form.get('skip_existing'):
                cmd.append('--skip-existing')
            if request.form.get('disable_redaction'):
                cmd.append('--disable-redaction')
            env = os.environ.copy()
            env["PYTHONPATH"] = os.path.abspath(os.path.dirname(__file__))
            job_id = str(uuid.uuid4())
            jobs[job_id] = {'progress': 0, 'log': '', 'done': False, 'audio_url': f"/audio/{filename}"}
            t = threading.Thread(target=run_tts_with_progress, args=(cmd, env, job_id))
            t.start()
            return jsonify({'job_id': job_id})
    # GET request
    return render_template_string(HTML)

@app.route('/progress/<job_id>')
def progress(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'progress': 0, 'log': '', 'done': True, 'audio_url': None})
    resp = {
        'progress': job['progress'],
        'log': job['log'],
        'done': job['done'],
        'audio_url': job['audio_url'] if job['done'] else None
    }
    return jsonify(resp)

@app.route('/audio/<filename>')
def audio(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=False)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
