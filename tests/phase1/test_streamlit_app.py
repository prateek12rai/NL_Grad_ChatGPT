"""Phase 1.5.3 — Streamlit app loads without runtime errors."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock


def test_streamlit_app_imports_without_error():
    root = Path(__file__).resolve().parents[2]
    app_path = root / "backend" / "streamlit_app.py"
    src = root / "src"

    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    # Mock Streamlit so import does not require a running server
    mock_st = MagicMock()
    mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
    sys.modules["streamlit"] = mock_st

    spec = importlib.util.spec_from_file_location("streamlit_app", app_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    mock_st.set_page_config.assert_called_once()
    mock_st.title.assert_called()
