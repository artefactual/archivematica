from django.contrib import admin
from fpr import models

admin.site.register(models.Format)
admin.site.register(models.FormatGroup)
admin.site.register(models.FormatVersion)
admin.site.register(models.IDCommand)
admin.site.register(models.IDRule)
admin.site.register(models.IDTool)
admin.site.register(models.FPRule)
admin.site.register(models.FPCommand)
admin.site.register(models.FPTool)

# admin.site.register(models.Agent)
# admin.site.register(models.CommandType)
# admin.site.register(models.Command)
# admin.site.register(models.CommandsSupportedBy)
# admin.site.register(models.FileIDType)
# admin.site.register(models.FileID)
# admin.site.register(models.CommandClassification)
# admin.site.register(models.CommandRelationship)
# admin.site.register(models.FileIDsBySingleID)
