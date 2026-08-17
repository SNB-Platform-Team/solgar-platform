"""Database routers: send reference + doctor models to the external DB."""


class ReferenceRouter:
    """
    Route external-DB models to `refdb`; everything else uses `default`.

    - ProductGroup, AddressGroup: read-only reference tables (solgar_tst).
    - Doctor (doctor_data): read *and* write — the Doctor Entry & Update
      screen inserts, updates and deletes rows directly in the external DB.
    """

    # Read-only reference models.
    reference_models = {"productgroup", "addressgroup"}

    # Models that live in the external DB and are also written to.
    external_write_models = {"doctor", "pharmacysolgar", "pharmacybounty"}

    def _external_models(self):
        """All model names that live in refdb (read side)."""
        return self.reference_models | self.external_write_models

    def db_for_read(self, model, **hints):
        """Read reference + doctor models from refdb, all else from default."""
        if model._meta.model_name in self._external_models():
            return "refdb"
        return None

    def db_for_write(self, model, **hints):
        """
        Doctor writes go to refdb. Reference models are not written in
        practice, but if they were, they'd also target refdb (never default).
        Everything else writes to default.
        """
        if model._meta.model_name in self._external_models():
            return "refdb"
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Never migrate external models (managed=False, external DB)."""
        if model_name in self._external_models():
            return False
        return None
