"""
Reusable chart generators for report-generator's visual PDF pipeline.
Adapted from the company-thesis-report skill's charts.py. Every function
saves a transparent-background PNG at the given path and returns that path.
Keep the visual language consistent across reports:
  navy   #1F4E78  - primary metric (revenue, price)
  teal   #1D9E75  - positive / profit / on-track / delivered
  red    #E24B4A  - negative / loss / delayed / missed
  amber  #BA7517  - caution / pending / mixed
  gray   #888888  - neutral reference line (e.g. benchmark)
  purple #534AB7  - DII / secondary series

Usage from the report-drafting step (see reference/report_format.md's
"Assembly" section):
    import sys; sys.path.insert(0, '<skill_dir>/scripts')
    from charts import revenue_profit_chart, quarterly_trend_chart, \
        shareholding_chart, before_after_chart, donut_chart, line_compare_chart

Install note: matplotlib is not bundled with this plugin — install once with
`pip install matplotlib --break-system-packages` if missing.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

NAVY = '#1F4E78'
TEAL = '#1D9E75'
RED = '#E24B4A'
AMBER = '#BA7517'
GRAY = '#888888'
PURPLE = '#534AB7'

plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 8,
    'axes.edgecolor': '#cccccc',
})


def _clean_axes(ax):
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.tick_params(labelsize=7.5)
    ax.grid(axis='y', color='#eeeeee', linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)


def revenue_profit_chart(path, periods, revenue, profit, revenue_label='Revenue (₹ Cr)', profit_label='Net profit (₹ Cr)', figsize=(9.2, 3.2)):
    """Dual-panel bar charts: revenue history (navy) and profit history (teal/red by sign)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, dpi=200)
    ax1.bar(periods, revenue, color=NAVY, zorder=3)
    ax1.set_title(revenue_label, fontsize=9, loc='left', color='#333')
    _clean_axes(ax1)
    ax1.tick_params(axis='x', rotation=45)

    colors = [TEAL if v >= 0 else RED for v in profit]
    ax2.bar(periods, profit, color=colors, zorder=3)
    ax2.axhline(0, color='#999', linewidth=0.8)
    ax2.set_title(profit_label, fontsize=9, loc='left', color='#333')
    _clean_axes(ax2)
    ax2.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig(path, transparent=True, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    return path


def quarterly_trend_chart(path, quarters, values, label='Revenue (₹ Cr)', color=NAVY, figsize=(9.2, 2.6)):
    """Single-panel bar chart for a recent quarterly trend (revenue, profit, or margin)."""
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    colors = [color if v >= 0 else RED for v in values] if any(v < 0 for v in values) else color
    ax.bar(quarters, values, color=colors, zorder=3)
    if any(v < 0 for v in values):
        ax.axhline(0, color='#999', linewidth=0.8)
    ax.set_title(label, fontsize=9, loc='left', color='#333')
    _clean_axes(ax)
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(path, transparent=True, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    return path


def shareholding_chart(path, periods, promoter, fii, dii, public, figsize=(9.2, 3.0)):
    """Stacked bar chart of shareholding pattern (%) over time."""
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    bottoms = [0] * len(periods)
    for series, color, label in [
        (promoter, NAVY, 'Promoter'), (fii, TEAL, 'FII'),
        (dii, PURPLE, 'DII'), (public, '#cccccc', 'Public/other'),
    ]:
        ax.bar(periods, series, bottom=bottoms, color=color, label=label, zorder=3)
        bottoms = [b + v for b, v in zip(bottoms, series)]
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=4, fontsize=7.5, frameon=False)
    _clean_axes(ax)
    ax.tick_params(axis='x', rotation=0)
    plt.tight_layout()
    plt.savefig(path, transparent=True, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    return path


def before_after_chart(path, metric_pairs, figsize=(9.2, 2.8)):
    """
    Grouped bar chart comparing a 'before' vs 'after' value for several metrics
    (e.g. capacity/revenue pre- and post-capex, net worth pre/post a
    recapitalization).
    metric_pairs: list of (label, before_value, after_value)
    """
    labels = [m[0] for m in metric_pairs]
    before = [m[1] for m in metric_pairs]
    after = [m[2] for m in metric_pairs]
    x = range(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    ax.bar([i - width / 2 for i in x], before, width, color='#cccccc', label='Before', zorder=3)
    ax.bar([i + width / 2 for i in x], after, width, color=NAVY, label='After', zorder=3)
    ax.axhline(0, color='#999', linewidth=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=8)
    ax.legend(loc='upper right', fontsize=7.5, frameon=False)
    _clean_axes(ax)
    plt.tight_layout()
    plt.savefig(path, transparent=True, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    return path


def donut_chart(path, labels, values, figsize=(4.2, 4.2)):
    """Donut chart for a capital/ownership breakdown (e.g. fund-raise allottees)."""
    palette = [NAVY, TEAL, PURPLE, AMBER, '#7F77DD', '#5DCAA5', '#D85A30', '#cccccc']
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    wedges, _, autotexts = ax.pie(
        values, labels=None, autopct=lambda p: f'{p:.0f}%' if p >= 5 else '',
        colors=palette[:len(values)], startangle=90, pctdistance=0.8,
        wedgeprops=dict(width=0.38, edgecolor='white'),
    )
    for t in autotexts:
        t.set_fontsize(7.5)
        t.set_color('white')
    ax.legend(wedges, labels, loc='center left', bbox_to_anchor=(1.0, 0.5), fontsize=7.5, frameon=False)
    ax.set_aspect('equal')
    plt.tight_layout()
    plt.savefig(path, transparent=True, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    return path


def line_compare_chart(path, periods, series_dict, ylabel='', figsize=(9.2, 2.8)):
    """
    Line chart comparing multiple series over time (e.g. stock return vs a
    sector index, or segment revenue lines).
    series_dict: {label: [values...]}, first entry drawn in navy, rest in
    teal/amber/gray/purple.
    """
    colors = [NAVY, TEAL, AMBER, GRAY, PURPLE]
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    for i, (label, values) in enumerate(series_dict.items()):
        ax.plot(periods, values, color=colors[i % len(colors)], linewidth=1.8, marker='o', markersize=3, label=label)
    ax.axhline(0, color='#ccc', linewidth=0.7)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8)
    ax.legend(loc='upper left', fontsize=7.5, frameon=False)
    _clean_axes(ax)
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(path, transparent=True, bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)
    return path
