(function(){

  var dx = {
    replace: function(elem, target, uri, method, outer) {
      window.event.preventDefault();
      window.event.stopPropagation();

      var target_node = document.querySelector(target);

      // if this is in a form, and method is post, capture the form data
      var cur = elem;
      var form = null;
      while (cur != document.body) {
        if (cur.nodeName == 'FORM') {
          form = cur;
          break;
        }
        cur = cur.parentNode;
      }

      function reshandler(response) {
        console.log(response);
        if (!response.ok) {
          return
        }
        response.text().then(data => {
          if (outer) {
            target_node.outerHTML = data;
          } else {
            target_node.innerHTML = data;
          }
        });
      }

      options = {};

      if (method === 'post') {
        options.method = 'POST';
        if (form != null) {
          options.body = new FormData(form);
        }
      }
      else if (method == 'get') {
        if (form != null) {
          var fd = new FormData(form);
          var fs = new URLSearchParams(fd).toString();
          uri += '?' + fs;
        }
      }
      // xhr.send(new FormData(oFormElement));

      fetch(uri, options).then(reshandler);
      return false;
    }
  };

  window.dx = dx;
})();
