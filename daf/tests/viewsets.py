from django.contrib.auth.models import User
from rest_framework import permissions
from rest_framework import serializers
from rest_framework import viewsets

import daf.rest_framework
from daf.tests.actions import grant_staff_access


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField()
    email = serializers.CharField()
    is_staff = serializers.BooleanField()


class UserViewSet(daf.rest_framework.ActionMixin, viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer
    daf_actions = [grant_staff_access.GrantStaffAccessObjectDRFAction]
