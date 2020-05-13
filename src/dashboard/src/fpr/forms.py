# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django import forms
from django.utils.translation import ugettext_lazy as _

from fpr import models as fprmodels


# ########## FORMATS ############


class FormatForm(forms.ModelForm):
    group = forms.ChoiceField(widget=forms.Select(attrs={"class": "form-control"}))

    def __init__(self, *args, **kwargs):
        super(FormatForm, self).__init__(*args, **kwargs)
        # add 'create' option to the FormatGroup dropdown
        choices = [(f.uuid, f.description) for f in fprmodels.FormatGroup.objects.all()]
        choices.insert(0, ("", "---------"))
        choices.append(("new", _("Create New")))
        self.fields["group"].choices = choices
        if hasattr(self.instance, "group") and self.instance.group:
            self.fields["group"].initial = self.instance.group.uuid
        # add Bootstrap class to description field
        self.fields["description"].widget.attrs["class"] = "form-control"

    class Meta:
        model = fprmodels.Format
        fields = ("description",)


class FormatVersionForm(forms.ModelForm):
    class Meta:
        model = fprmodels.FormatVersion
        fields = (
            "description",
            "version",
            "pronom_id",
            "access_format",
            "preservation_format",
        )


class FormatGroupForm(forms.ModelForm):
    class Meta:
        model = fprmodels.FormatGroup
        fields = ("description",)


# ########## ID TOOLS ############


class IDToolForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(IDToolForm, self).clean()
        if (
            self.instance.pk is None
            and fprmodels.IDTool.objects.filter(
                description=cleaned_data.get("description"),
                version=cleaned_data.get("version"),
            ).exists()
        ):
            raise forms.ValidationError(
                _("An ID tool with this description and version already" " exists")
            )
        return cleaned_data

    class Meta:
        model = fprmodels.IDTool
        fields = ("description", "version")


class IDCommandForm(forms.ModelForm):
    class Meta:
        model = fprmodels.IDCommand
        fields = ("tool", "description", "config", "script_type", "script")


# ########## ID RULES ############


class IDRuleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(IDRuleForm, self).__init__(*args, **kwargs)
        # Limit to only enabled formats/commands
        self.fields["format"].queryset = fprmodels.FormatVersion.active.all()
        self.fields["command"].queryset = fprmodels.IDCommand.active.all()

    class Meta:
        model = fprmodels.IDRule
        fields = ("format", "command", "command_output")


# ########## FP RULES ############


class FPRuleForm(forms.ModelForm):
    command = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(FPRuleForm, self).__init__(*args, **kwargs)

        # Add 'create' option to the FPCommand dropdown
        # Do not include event detail or verification, since those are not run
        # through FPRules normally
        commands = fprmodels.FPCommand.active.exclude(
            command_usage="event_detail"
        ).exclude(command_usage="verification")
        choices = [(f.uuid, f.description) for f in commands]
        choices.insert(0, ("", "---------"))
        choices.append(("new", _("Create New")))
        self.fields["command"].choices = choices
        if hasattr(self.instance, "command"):
            self.fields["command"].initial = self.instance.command.uuid

        # Show only active format versions in the format dropdown
        self.fields["format"].queryset = fprmodels.FormatVersion.active.all()

    def clean(self):
        cleaned_data = super(FPRuleForm, self).clean()
        if self.instance.pk is None:
            try:
                existing_fprule = fprmodels.FPRule.objects.get(
                    purpose=cleaned_data.get("purpose"),
                    format=cleaned_data.get("format"),
                    command=cleaned_data.get("command"),
                )
            except fprmodels.FPRule.DoesNotExist:
                return cleaned_data
            # If there is an existing matching rule, the error message should
            # give its UUID so that the user can reasonably track it down.
            else:
                ex_fpr_uuid = existing_fprule.uuid
                msg = _(
                    "An identical FP rule already exists. See rule" " %(uuid)s."
                ) % {"uuid": ex_fpr_uuid}
                if not existing_fprule.enabled:
                    replacers = fprmodels.FPRule.objects.filter(
                        replaces=existing_fprule.uuid
                    ).all()
                    if replacers:
                        msg += _(
                            " Rule %(uuid)s is disabled and has been"
                            " replaced by the following rule(s):"
                            " %(repl_uuids)s"
                        ) % {
                            "uuid": ex_fpr_uuid,
                            "repl_uuids": ", ".join([r.uuid for r in replacers]),
                        }
                    else:
                        msg += _(" Rule %(uuid)s is disabled.") % {"uuid": ex_fpr_uuid}
                raise forms.ValidationError(msg)
        return cleaned_data

    class Meta:
        model = fprmodels.FPRule
        fields = ("purpose", "format")


# ########## FP TOOLS ############


class FPToolForm(forms.ModelForm):
    class Meta:
        model = fprmodels.FPTool
        fields = ("description", "version")


class FPCommandForm(forms.ModelForm):

    use_required_attribute = False

    def __init__(self, *args, **kwargs):
        super(FPCommandForm, self).__init__(*args, **kwargs)

        verification_commands = fprmodels.FPCommand.active.filter(
            command_usage="verification"
        )
        event_detail_commands = fprmodels.FPCommand.active.filter(
            command_usage="event_detail"
        )

        # don't allow self-relation
        if hasattr(self.instance, "uuid"):
            verification_commands = verification_commands.exclude(
                uuid=self.instance.uuid
            )
            event_detail_commands = event_detail_commands.exclude(
                uuid=self.instance.uuid
            )

        self.fields["verification_command"].queryset = verification_commands
        self.fields["event_detail_command"].queryset = event_detail_commands

    class Meta:
        model = fprmodels.FPCommand
        fields = (
            "tool",
            "description",
            "command",
            "script_type",
            "output_format",
            "output_location",
            "command_usage",
            "verification_command",
            "event_detail_command",
        )
