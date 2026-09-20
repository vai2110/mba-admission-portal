(function(){
  if(window.__collegeDecodedGuidanceLoaded)return;
  window.__collegeDecodedGuidanceLoaded=true;

  var KEY='collegeDecodedGuidanceShownV2:'+location.pathname;
  var pageTitle=document.title||'CollegeDecoded';
  var pageUrl=window.location.href;

  function build(){
    if(document.getElementById('cdGuidanceModal'))return;

    var cta=document.createElement('section');
    cta.className='cd-guidance-cta';
    cta.innerHTML='<div><strong>🎓 Confused about your college options?</strong><p>Get personalised guidance based on what you are looking for.</p></div><button type="button" class="cd-guidance-open">Get Free Guidance →</button>';

    var main=document.querySelector('main');
    if(main){
      var sections=main.querySelectorAll(':scope > section');
      if(sections.length>1) sections[1].after(cta);
      else main.appendChild(cta);
    }else{
      document.body.appendChild(cta);
    }

    var modal=document.createElement('div');
    modal.id='cdGuidanceModal';
    modal.className='cd-guidance-modal';
    modal.setAttribute('aria-hidden','true');
    modal.innerHTML='<div class="cd-guidance-backdrop" data-cd-close></div>'+
      '<div class="cd-guidance-dialog" role="dialog" aria-modal="true" aria-labelledby="cdGuidanceTitle">'+
      '<button type="button" class="cd-guidance-close" data-cd-close aria-label="Close">×</button>'+
      '<div class="cd-guidance-head"><div><h2 id="cdGuidanceTitle">🎓 Confused about your college options?</h2><p>Tell us what you are looking for. We will help you explore your options.</p></div><div class="cd-guidance-badge">FREE GUIDANCE</div></div>'+
      '<form class="cd-guidance-form" id="cdGuidanceForm">'+
      '<div class="cd-guidance-field cd-full"><label>What are you looking for?</label><div class="cd-choice-row">'+
      '<label class="cd-choice"><input type="radio" name="cd_interest" value="MBA / PGDM" required><span>MBA / PGDM</span></label>'+
      '<label class="cd-choice"><input type="radio" name="cd_interest" value="Engineering"><span>Engineering</span></label>'+
      '<label class="cd-choice"><input type="radio" name="cd_interest" value="Medical"><span>Medical</span></label>'+
      '<label class="cd-choice"><input type="radio" name="cd_interest" value="Other"><span>Other</span></label></div></div>'+
      '<div class="cd-guidance-field"><label>Exam &amp; Score <em>(optional)</em></label><input name="cd_score" type="text" placeholder="e.g. CAT – 95 percentile"></div>'+
      '<div class="cd-guidance-field"><label>What do you need help with?</label><select name="cd_help" required><option value="">Select one</option><option>Find colleges</option><option>Compare colleges</option><option>Admission guidance</option><option>Fees & placements</option><option>Not sure</option></select></div>'+
      '<div class="cd-guidance-field"><label>WhatsApp Number</label><input name="cd_whatsapp" type="tel" inputmode="numeric" autocomplete="tel" placeholder="+91 98XXXXXXXX" pattern="[0-9+() -]{10,16}" required></div>'+
      '<div class="cd-guidance-field"><label>Your Name</label><input name="cd_name" type="text" autocomplete="name" placeholder="Your name" required></div>'+
      '<input type="hidden" name="cd_source_page" value="">'+
      '<button class="cd-guidance-submit" type="submit">Get Free Guidance →</button></form>'+
      '<div class="cd-guidance-note">We only use these details to respond to your guidance request. No spam.</div>'+
      '<div class="cd-guidance-success" id="cdGuidanceSuccess">Thanks! Your guidance request has been recorded for testing. We will connect the enquiry submission after the layout is approved.</div>'+
      '</div>';
    document.body.appendChild(modal);

    var form=document.getElementById('cdGuidanceForm');
    form.elements.cd_source_page.value=pageUrl;
    var openers=document.querySelectorAll('.cd-guidance-open');
    var shown=false;
    var lastY=window.scrollY||0;

    function show(force){
      if(!force && (shown||sessionStorage.getItem(KEY)==='1'))return;
      shown=true;
      sessionStorage.setItem(KEY,'1');
      modal.classList.add('cd-open');\n      modal.style.display='flex';
      modal.setAttribute('aria-hidden','false');
      document.body.style.overflow='hidden';
      setTimeout(function(){var first=form.querySelector('input:not([type=hidden])');if(first)first.focus();},50);
    }
    function close(){
      modal.classList.remove('cd-open');\n      modal.style.display='none';
      modal.setAttribute('aria-hidden','true');
      document.body.style.overflow='';
      sessionStorage.setItem(KEY,'1');
    }

    openers.forEach(function(b){b.addEventListener('click',function(){show(true);});});
    modal.querySelectorAll('[data-cd-close]').forEach(function(x){x.addEventListener('click',close);});
    document.addEventListener('keydown',function(e){if(e.key==='Escape'&&modal.classList.contains('cd-open'))close();});

    form.addEventListener('submit',function(e){
      e.preventDefault();
      if(!form.checkValidity()){form.reportValidity();return;}
      document.getElementById('cdGuidanceSuccess').style.display='block';
      form.querySelectorAll('input,select,button').forEach(function(x){x.disabled=true;});
    });

    function autoCheck(){
      if(shown||sessionStorage.getItem(KEY)==='1')return;
      var y=window.scrollY||document.documentElement.scrollTop||0;
      var scrollable=Math.max(1,document.documentElement.scrollHeight-window.innerHeight);
      var mobile=window.innerWidth<=640;
      var px=mobile?600:1000;
      var depth=mobile?0.40:0.40;
      if(y>=px || y/scrollable>=depth)show(false);
    }
    window.addEventListener('scroll',autoCheck,{passive:true});
    window.addEventListener('touchend',autoCheck,{passive:true});
    var watcher=setInterval(function(){
      if(shown||sessionStorage.getItem(KEY)==='1'){clearInterval(watcher);return;}
      autoCheck();
    },300);
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',build);
  else build();
})();