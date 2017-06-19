$(document).ready(function() {
  var $selects = $('select');

  $selects.find('option[value=""]').attr('disabled', true);
  $selects.material_select();
  $('.modal').modal();

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
});

