"""
Desktop entry point for MonitorAI.
freeze_support() MUST be called before anything else so that PyInstaller
multiprocessing worker processes are handled correctly on Windows.
"""
import multiprocessing
import sys
import os

if __name__ == '__main__':
    # Must be first — lets PyInstaller redirect spawned worker processes
    # to their target function without re-running main().
    multiprocessing.freeze_support()

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    from src.main import main
    main()
