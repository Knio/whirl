(function(){

  var dx = {
    replace: function(target, uri) {
      var target_node = document.querySelector(target);
      fetch(uri)
        .then(response => {
          console.log(response);
          if (!response.ok) {
            return;
          }
          response.text().then(data => {
            target_node.innerHTML = data;
          })
        });
    }
  };

  window.dx = dx;
})();
