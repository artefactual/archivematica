# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings

def data_migration(apps, schema_editor):
    Agent = apps.get_model('main', 'Agent')
    Event = apps.get_model('main', 'Event')
    UserProfile = apps.get_model('main', 'UserProfile')
    User = apps.get_model('auth', 'User')

    # Create Agents for all Users
    for u in User.objects.all():
        agent = Agent.objects.create(
            identifiertype='Archivematica user pk',
            identifiervalue=str(u.id),
            name='username="{u.username}", first_name="{u.first_name}", last_name="{u.last_name}"'.format(u=u),
            agenttype='Archivematica user',
        )
        UserProfile.objects.create(user=u, agent=agent)

    # Add Agents list to all Events
    system_agent = Agent.objects.get(pk=1)
    org_agent = Agent.objects.get(pk=2)
    for e in Event.objects.all():
        e.agents.add(system_agent, org_agent)
        user_agent = Agent.objects.get(userprofile__user_id=e.linking_agent)
        e.agents.add(user_agent)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0023_normalization_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='agents',
            field=models.ManyToManyField(to='main.Agent'),
            preserve_default=True,
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('agent', models.OneToOneField(to='main.Agent')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'main_userprofile',
            },
            bases=(models.Model,),
        ),

        migrations.RunPython(data_migration),

        migrations.RemoveField(
            model_name='event',
            name='linking_agent',
        ),

    ]
