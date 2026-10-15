"""kltool — Bo‘g‘imTahlil uchun umumiy AI moduli.

Training, baholash va backend inference bir xil kodni (preprocess, arxitektura,
checkpoint formati, Grad-CAM) ishlatishi uchun shu paketda jamlangan.
"""

KL_CLASSES: tuple[str, ...] = ("KL0", "KL1", "KL2", "KL3", "KL4")
NUM_CLASSES = len(KL_CLASSES)

__all__ = ["KL_CLASSES", "NUM_CLASSES"]
