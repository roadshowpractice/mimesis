import json
import hashlib
from difflib import SequenceMatcher
from pathlib import Path

INPUT_FILE = Path('tests/inputs/tim_ballard_video_tasks.json')


def fake_download(url: str, dest: Path) -> Path:
    """Simulate downloading a video by creating a text file."""
    name = hashlib.md5(url.encode()).hexdigest() + '.txt'
    path = dest / name
    path.write_text(f"fake video content for {url}\n")
    return path


def fake_transcribe(video_path: Path) -> str:
    """Return the contents of the fake video file."""
    return video_path.read_text()


def similarity(text_a: str, text_b: str) -> float:
    matcher = SequenceMatcher(None, text_a, text_b)
    return matcher.ratio()


def test_download_and_compare(tmp_path: Path):
    data = json.loads(INPUT_FILE.read_text())
    urls = [entry['url'] for entry in data[:3]]

    transcripts = []
    for url in urls:
        video_file = fake_download(url, tmp_path)
        transcripts.append(fake_transcribe(video_file))

    results = []
    for i in range(len(transcripts)):
        for j in range(i + 1, len(transcripts)):
            results.append(similarity(transcripts[i], transcripts[j]))

    assert len(results) == 3
    for score in results:
        assert 0.0 <= score <= 1.0
