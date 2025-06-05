"""
Visualization utilities for stress test results
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Optional, List
import numpy as np


def plot_stress_results(df: pd.DataFrame, title: Optional[str] = None,
                        figsize: tuple = (12, 6)) -> plt.Figure:
    """
    Plot stress test results showing P&L across stress levels

    Args:
        df: DataFrame from stress test results
        title: Plot title
        figsize: Figure size

    Returns:
        matplotlib Figure
    """
    # Extract P&L columns (those that can be converted to float)
    pnl_columns = []
    for col in df.columns:
        try:
            float(col)
            pnl_columns.append(col)
        except ValueError:
            continue

    # Sort columns by stress level
    pnl_columns.sort(key=float)

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot each position
    for idx, row in df.iterrows():
        if row['instrument_type'] != 'AGGREGATE':
            label = f"{row['underlying']} - {row['position_id']}"
            stress_levels = [float(col) for col in pnl_columns]
            pnl_values = [row[col] for col in pnl_columns]

            ax.plot(stress_levels, pnl_values, marker='o', label=label, linewidth=2)

    # Add aggregate lines with different style
    for idx, row in df.iterrows():
        if row['instrument_type'] == 'AGGREGATE':
            label = f"AGG: {row['underlying']}"
            stress_levels = [float(col) for col in pnl_columns]
            pnl_values = [row[col] for col in pnl_columns]

            ax.plot(stress_levels, pnl_values, marker='s', label=label,
                    linewidth=3, linestyle='--', markersize=8)

    # Formatting
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)

    ax.set_xlabel('Stress Level', fontsize=12)
    ax.set_ylabel('P&L ($)', fontsize=12)
    ax.set_title(title or 'Stress Test Results', fontsize=14, fontweight='bold')

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

    # Add grid
    ax.grid(True, alpha=0.3)

    # Legend
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    return fig


def plot_scenario_comparison(results_dict: Dict[str, pd.DataFrame],
                             underlying: str = None,
                             position_id: str = None) -> plt.Figure:
    """
    Compare results across multiple scenarios for specific positions

    Args:
        results_dict: Dict of scenario_name -> DataFrame
        underlying: Filter by underlying (optional)
        position_id: Filter by position_id (optional)

    Returns:
        matplotlib Figure
    """
    fig, axes = plt.subplots(len(results_dict), 1, figsize=(12, 4 * len(results_dict)))

    if len(results_dict) == 1:
        axes = [axes]

    for idx, (scenario_name, df) in enumerate(results_dict.items()):
        ax = axes[idx]

        # Filter data if requested
        plot_df = df.copy()
        if underlying:
            plot_df = plot_df[plot_df['underlying'] == underlying]
        if position_id:
            plot_df = plot_df[plot_df['position_id'] == position_id]

        # Extract P&L columns
        pnl_columns = []
        for col in plot_df.columns:
            try:
                float(col)
                pnl_columns.append(col)
            except ValueError:
                continue

        pnl_columns.sort(key=float)

        # Plot
        for _, row in plot_df.iterrows():
            if row['instrument_type'] != 'AGGREGATE':
                label = f"{row['underlying']} - {row['position_id']}"
                stress_levels = [float(col) for col in pnl_columns]
                pnl_values = [row[col] for col in pnl_columns]

                ax.plot(stress_levels, pnl_values, marker='o', label=label)

        ax.set_title(f'{scenario_name}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Stress Level')
        ax.set_ylabel('P&L ($)')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax.legend()

    plt.tight_layout()
    return fig


def create_pnl_heatmap(df: pd.DataFrame, title: Optional[str] = None) -> plt.Figure:
    """
    Create a heatmap of P&L values across positions and stress levels

    Args:
        df: DataFrame from stress test results
        title: Plot title

    Returns:
        matplotlib Figure
    """
    # Extract P&L columns
    pnl_columns = []
    for col in df.columns:
        try:
            float(col)
            pnl_columns.append(col)
        except ValueError:
            continue

    pnl_columns.sort(key=float)

    # Create matrix for heatmap
    position_labels = []
    pnl_matrix = []

    for _, row in df.iterrows():
        if row['instrument_type'] != 'AGGREGATE':
            position_labels.append(f"{row['underlying']}-{row['position_id']}")
            pnl_matrix.append([row[col] for col in pnl_columns])

    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, max(6, len(position_labels) * 0.5)))

    # Create heatmap with diverging colormap centered at 0
    vmax = max(abs(np.array(pnl_matrix).min()), abs(np.array(pnl_matrix).max()))

    sns.heatmap(pnl_matrix,
                xticklabels=[f"{float(col):.1%}" for col in pnl_columns],
                yticklabels=position_labels,
                center=0,
                cmap='RdYlGn',
                vmin=-vmax,
                vmax=vmax,
                annot=True,
                fmt='.0f',
                cbar_kws={'label': 'P&L ($)'},
                ax=ax)

    ax.set_title(title or 'P&L Heatmap', fontsize=14, fontweight='bold')
    ax.set_xlabel('Stress Level', fontsize=12)
    ax.set_ylabel('Position', fontsize=12)

    plt.tight_layout()
    return fig


def summarize_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summary table of stress test results

    Args:
        df: DataFrame from stress test results

    Returns:
        Summary DataFrame
    """
    # Extract P&L columns
    pnl_columns = []
    for col in df.columns:
        try:
            float(col)
            pnl_columns.append(col)
        except ValueError:
            continue

    # Create summary
    summary_data = []

    for _, row in df.iterrows():
        if row['instrument_type'] == 'AGGREGATE':
            pnl_values = [row[col] for col in pnl_columns]

            summary_data.append({
                'Underlying': row['underlying'],
                'Max Loss': min(pnl_values),
                'Max Loss Stress': pnl_columns[pnl_values.index(min(pnl_values))],
                'Max Gain': max(pnl_values),
                'Max Gain Stress': pnl_columns[pnl_values.index(max(pnl_values))],
                'Range': max(pnl_values) - min(pnl_values)
            })

    return pd.DataFrame(summary_data)