(function(){
  'use strict';
  function init(){
    document.querySelectorAll('.mobile-on-page details > a[href^="#"]').forEach(function(link){
      link.addEventListener('click',function(){
        var details=link.closest('details');
        if(details){ details.open=false; }
      });
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init); else init();
})();
