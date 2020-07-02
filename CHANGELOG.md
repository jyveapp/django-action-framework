# Changelog
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

