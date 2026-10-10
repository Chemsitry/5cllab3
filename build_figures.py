"""Compile editable figure sources and the report using an installed LaTeX.

PNG previews require pypdfium2. SVG conversion is optional and uses pdftocairo.
No packages or external content are downloaded by this script.
"""
from pathlib import Path
import shutil
import subprocess


def build():
    root = Path(__file__).resolve().parent
    from analyze_lab3 import run_analysis
    from make_experiment5_fit import write_figure
    write_figure(run_analysis(root), root)
    latex = shutil.which('pdflatex')
    if latex is None:
        raise SystemExit('pdflatex was not found. Add your LaTeX installation to the path.')
    cairo = shutil.which('pdftocairo')
    try:
        import pypdfium2 as pdfium
    except ImportError:
        pdfium = None
    for source in sorted((root/'figures').glob('*.tex')) + [root/'main.tex']:
        rounds = 2 if source.name == 'main.tex' else 1
        for _ in range(rounds):
            command = [latex, '-interaction=nonstopmode', '-halt-on-error', source.name]
            if 'miktex' in latex.lower():
                command.insert(1, '--disable-installer')
            subprocess.run(command, cwd=source.parent, check=True)
        if source.parent.name == 'figures':
            if pdfium is not None:
                with pdfium.PdfDocument(source.with_suffix('.pdf')) as document:
                    document[0].render(scale=3).to_pil().save(source.with_suffix('.png'))
            if cairo is not None:
                subprocess.run([cairo, '-svg', str(source.with_suffix('.pdf')),
                                str(source.with_suffix('.svg'))], check=True)
    print('Figures and main.pdf rebuilt.')


if __name__ == '__main__':
    build()
