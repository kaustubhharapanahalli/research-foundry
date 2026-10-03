"""Enable pgvector, so any app can declare a VectorField."""

from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    """Create the vector extension; it needs a superuser or the owner."""

    operations = [VectorExtension()]
