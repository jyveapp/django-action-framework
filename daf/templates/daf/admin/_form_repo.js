{% comment %}
  A javascript module for persisting form values between page
  reloads.
  Adopted from https://gist.github.com/zaus/4717416
{% endcomment %}

var FormRepo = function (namespace) {''
  this.N = namespace + '.' + window.location.pathname;
};
django.jQuery.extend(FormRepo.prototype, {
  namespace: function (key) {
    return this.N + '.' + key;
  },
  preserve: function ($form, iden) {
    var data = $form.serializeArray();

    localStorage.setItem(
      this.namespace('form.' + (iden || $form.index())),
      JSON.stringify(data)
    );
  },
  restore: function ($form, iden) {
    var data = localStorage.getItem(
      this.namespace('form.' + (iden || $form.index()))
    );
    if (null == data || django.jQuery.isEmptyObject(data)) return;

    django.jQuery.each(JSON.parse(data), function (i, kv) {
      // Find form element, set its value
      var $input = $form.find('[name=' + kv.name + ']');
      if ($input.is(':checkbox') || $input.is(':radio')) {
        $input.filter(function () {
          return $(this).val() == kv.value;
        }).first().attr('checked', 'checked');
      } else {
        $input.val(kv.value);
      }
    });
  },
  remove: function ($form, iden) {
    localStorage.removeItem(
      this.namespace('form.' + (iden || $form.index()))
    );
  }
});
