$(document).ready(function() {
  var $selects = $('select');

  // Helper function to replace parameter in url.
  function replaceUrlParam(url, paramName, paramValue) {
    var pattern = new RegExp('\\b('+paramName+'=).*?(&|$)');

    if (paramValue === '') {
      // Remove param and & or ? on the end of the url.
      url = url.replace(pattern, '');
      url = url.replace(/[&?]$/, '');

      return url;
    }

    if (url.search(pattern) >= 0) {
      // Update param into the url.
      return url.replace(pattern, '$1' + paramValue + '$2');
    }

    // Insert param into the url.
    return url + (url.indexOf('?')>0 ? '&' : '?') + paramName + '=' + paramValue;
  }

  // Helper function to search user.
  function searchUser(e, value) {
    if (typeof value === 'undefined') {
      value = $(this).siblings('input').val();
    }
    window.location.href = replaceUrlParam(window.location.href, 'search', value);
  }

  // Initialize material select.
  $selects.find('option[value=""]').attr('disabled', true);
  $selects.material_select();
  $('.modal').modal();

  // User delete dialog.
  $('.user-delete-dialog').click(function(e) {
    var $modal = $('#delete-modal');
    var uid = $(this).data('uid');
    var selector;
    var $user_row;

    e.preventDefault();
    $modal.modal('open');

    $modal.find('.action-delete').off('click.delete-user').on('click.delete-user', function(e) {
      e.preventDefault();
      $modal.modal('close');
      selector = '#user-' + uid;
      $user_row = $(selector);
      $user_row.fadeOut();

      $.ajax({
        url: '/user/' + uid,
        type: 'DELETE',
        success: function(result) {
          $user_row.remove();
        },
        error: function(result) {
          $user_row.fadeIn();
        }
      });
    });
  });

  // Reload page and show needed amount of items per page.
  $('select.items-per-page').change(function() {
    window.location.href = replaceUrlParam(window.location.href, 'items', this.value);
  });

  // Clean search field.
  $('.user-search .close').click(function() {
    $(this).siblings('input').val('');
  });

  // Search given string in user names.
  $('.user-search label').click(searchUser);
  $('.user-search input').keypress(function(e) {
    if (e.which === 13) {
      searchUser(e, this.value);
    }
  });
});

