"""Regenerate the Experiment 5 fit figure source from full precision results."""
from pathlib import Path
from analyze_lab3 import run_analysis, maximum_coordinates


def coordinates(xs, ys, errors):
    return ' '.join(f'({x:.16g},{y:.16g}) +- (0,{error:.16g})'
                    for x, y, error in zip(xs, ys, errors))


def write_figure(results, root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    fits = results['double_slit']['linear_fits']
    z3 = maximum_coordinates()[2]
    panels = []
    for index, (name, xlabel, title, outer_x, outer_y, ymax) in enumerate([
        ('fine_224', r'Fine order $m$', 'Fine fringes', 3., .65, .95),
        ('envelope_224', r'Maximum coordinate $z_n$', 'Envelope maxima', z3, 3.12, 3.55),
    ]):
        fit = fits[name]
        common = r'width=7.4cm,height=4.4cm,grid=major,grid style={gray!20},tick label style={font=\small},label style={font=\small},xmin=0,xmax=3.8'
        panel = r'''\begin{minipage}{.49\linewidth}\centering
\begin{tikzpicture}
\begin{axis}[COMMON,ymin=0,ymax=YMAX,xtick=XTICKS,xlabel={XLABEL},ylabel={Span / $\text{cm}$},title={TITLE},title style={font=\normalsize}]
\addplot[black,domain=0:LAST,samples=2]{SLOPE*x};
\addplot[black,dashed,domain=LAST:3.8,samples=2]{SLOPE*x};
\addplot[only marks,mark=*,mark size=2pt,error bars/.cd,y dir=both,y explicit] coordinates {USED};
\addplot[only marks,gray!75!black,mark=triangle,mark size=3pt,error bars/.cd,y dir=both,y explicit] coordinates {EXCLUDED};
\end{axis}
\end{tikzpicture}
\par\vspace{3pt}
\begin{tikzpicture}
\begin{axis}[COMMON,height=3.3cm,ymin=-1.4,ymax=1.6,ytick={-1,0,1},xtick=XTICKS,xlabel={XLABEL},ylabel={$r_i$}]
\addplot[gray,domain=0:3.8,samples=2]{0};
\addplot[only marks,mark=*,mark size=2pt,error bars/.cd,y dir=both,y explicit] coordinates {RESIDUALS};
\end{axis}
\end{tikzpicture}
\end{minipage}'''
        panel = panel.replace('COMMON', common).replace('YMAX', str(ymax))
        panel = panel.replace('XTICKS', '{1,2,3}' if index == 0 else '{1.5,2.5,3.5}')
        panel = panel.replace('XLABEL', xlabel).replace('TITLE', title)
        panel = panel.replace('SLOPE', format(fit['slope_cm'], '.16g'))
        panel = panel.replace('LAST', format(fit['coordinate'][-1], '.16g'))
        panel = panel.replace('USED', coordinates(fit['coordinate'], fit['measurements_cm'], fit['reading_scales_cm']))
        panel = panel.replace('EXCLUDED', coordinates([outer_x], [outer_y], [.2]))
        panel = panel.replace('RESIDUALS', coordinates(fit['coordinate'], fit['normalized_residuals'], [1., 1.]))
        panels.append(panel)
    content = panels[0]+r'\hfill'+'\n'+panels[1]
    wrapper = r'''\documentclass[border=4pt]{standalone}
\usepackage{amsmath,amssymb,textcomp,tikz,pgfplots}
\pgfplotsset{compat=1.18}
\begin{document}
\begin{minipage}{6.5in}\centering
CONTENT
\end{minipage}
\end{document}
'''
    path = root/'figures/experiment5_fits.tex'
    path.write_text(wrapper.replace('CONTENT', content), encoding='utf-8')
    return path


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    print(write_figure(run_analysis(root), root).name)
