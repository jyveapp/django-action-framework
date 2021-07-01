# Changelog
## 1.5.0 (2021-07-01)
### Bug
  - Don't override action methods on viewset classes [Wes Kendall, cc34e82]

    When DAF overrides the class definition with actions, it now will check
    if the action is already defined and ignore setting the class attribute.
    Previously it asserted it wasn't there and failed loudly, but that caused
    issues for subclasses. Overriding it also causes issues for subclasses.

    For now, we are ignoring adding the action if it is already defined.
    We may want to revisit this behavior in the future.
  - Removed a useless assert that caused errors [Wes Kendall, 98eea01]

    An extra-defensive assert was added in to the DAF action installer
    that caused errors whenever one would subclass DRF viewsets. This
    assert has been removed.

## 1.3.3 (2020-10-01)
### Trivial
  - README.rst: Mention other required apps [John Vandenberg, ad12876]

## 1.4.0 (2020-10-01)
### Bug
  - action.html: Hide inlines [John Vandenberg, c6a316d]

    Django admin inlines were being shown on the action forms.
    They are not relevant and unpredictable content, but removing them
    can break the admin form, so hiding them is the easy fix for
    all cases encountered thus far.

## 1.3.2 (2020-08-06)
### Trivial
  - Update all non-pinned dependencies [Tómas Árni Jónasson, 2f965df]
  - Update `django-args` to verion 1.4.0 which fixes a bug in multi-object forms [Tómas Árni Jónasson, f573d56]

## 1.3.1 (2020-08-04)
### Trivial
  - Add a missing import (only needed if `daf.rest_framework` is imported before `daf.registry` is imported) [Tómas Árni Jónasson, c621e30]
  - Move DRF import into a classmethod to avoid premature usage of Django settings [Tómas Árni Jónasson, 891fc44]

## 1.3.0 (2020-07-21)
### Bug
  - Avoid using Django settings in module top-level [Tómas Árni Jónasson, fb4ada7]

## 1.2.1 (2020-07-02)
### Trivial
  - Don't adapt python args validators to DRF action interface forms [Wes Kendall, 45011a4]

## 1.2.0 (2020-07-02)
### Bug
  - Adapts DRF action forms with django-args [Wes Kendall, ff0329b]

    DRF actions previously performed no adaptation of their forms using
    djarg.forms.adapt. This meant that any dynamic utilities like djarg.forms.Field
    would not work on DRF action forms.

## 1.1.1 (2020-07-02)
### Trivial
  - Attach additional exception context and fix display_name rendering from admin actions [Wes Kendall, 60b3686]

## 1.1.0 (2020-06-30)
### Feature
  - Add atomicity and locking to object actions. [Wes Kendall, 086c70c]

    By default, ``ObjectAction`` and ``ObjectsAction`` lock the object(s)
    being updated with a select_for_update and wrap the action in a transaction.
    Since this is done with the ``djarg.qset`` helper, transactions and locking
    will *not* happen when only running validations.

    This behavior was documented and can be turned off by setting the
    ``select_for_update`` attribute of actions to ``None``

## 1.0.1 (2020-06-29)
### Trivial
  - Added more information to the README [Wes Kendall, f775d1a]

## 1.0.0 (2020-06-25)
### Api-Break
  - Initial release of django-action-framework [Wes Kendall, 8ef57d1]

    django-action-framework (DAF) provides the ability to create actions from
    which a number of different interfaces can be built, including:

    1. Form views, update views, and bulk update views.
    2. Admin object actions, bulk object actions, and model page actions.
    3. DRF object actions.
    4. Wizard for all admin and normal form views.

    DAF is primarily built on top of python-args and django-args, which
    means that ``@arg.validators`` and other ``python-args`` decorators
    will work seamlessly with all DAF views and interfaces.

