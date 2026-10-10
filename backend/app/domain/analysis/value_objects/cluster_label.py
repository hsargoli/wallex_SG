"""ClusterLabel — برچسب انسانی یه خوشه.

KMeans عدد برمی‌گردونه (0,1,2,3). این VO به هر عدد
یه نام و توضیح انسانی می‌چسبونه.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClusterLabel:
    """برچسب یه خوشه (مثلاً «آروم»، «سقوط»)."""

    cluster_id: int
    name: str
    description: str
