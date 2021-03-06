$(document).ready(function () {
  var $calendarContent = $('#calendarContent');

  $calendarContent.on('click', 'ul li', function (event) {
    event.preventDefault();

    var context = {
      'csrfmiddlewaretoken': $('#csrf input').val(),
      'appointment-id': $(this).data('id'),
    };

    $.ajax({
      method: 'POST',
      url: '/booking/reschedule-submit/',
      data: context,
      statusCode: {
        200: function () {
          window.location.replace('/profile/');
        },
        500: function () {
          window.location.replace('/profile/');
        }
      },
    });
  });
});