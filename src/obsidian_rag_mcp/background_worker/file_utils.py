from hashlib import sha256
import subprocess
import tempfile
from pathlib import Path

def hash_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()



def compress_for_asr_tempdir(input_path: Path, bitrate: str = "32k"):
    temp_dir = Path(tempfile.gettempdir())
    output_path = temp_dir / f"{input_path.stem}.mp3"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-ac", "1",          # mono
        "-ar", "16000",      # 16 kHz
        "-c:a", "libmp3lame",
        "-b:a", bitrate,
        str(output_path)
    ]

    subprocess.run(cmd, check=True)
    return str(output_path)