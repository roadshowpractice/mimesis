import logging

def test_basic_log(tmp_path):
    log_file = tmp_path / "simple.log"
    logging.basicConfig(filename=log_file, level=logging.INFO, force=True)
    logging.info("Kilroy was here")
    assert log_file.exists(), "log file not created"
    assert "Kilroy was here" in log_file.read_text()
