import sys
import os
import pytest

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from core.signature import Signature
from ui.colors import ColorCycler

def test_signature_empty_start():
    sig = Signature()
    assert len(sig.wire_types) == 0
    assert len(sig.morphisms) == 0
    assert len(sig.relations) == 0

def test_add_morphism():
    sig = Signature()
    sig.add_morphism("MyOp", "Function", [{"type": "Image", "label": "img"}], [{"type": "Latent", "label": "lat"}])
    assert "MyOp" in sig.morphisms
    assert sig.morphisms["MyOp"].inputs[0]["type"] == "Image"

def test_add_relation():
    sig = Signature()
    sig.add_relation("Rel1", "M1", "M2", "KL")
    assert "Rel1" in sig.relations
    assert sig.relations["Rel1"].divergence == "KL"

def test_color_cycler():
    c1 = ColorCycler.next_color()
    c2 = ColorCycler.next_color()
    assert c1 != c2
    assert c1.startswith("#")
