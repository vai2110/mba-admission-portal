document.addEventListener('DOMContentLoaded',()=>{
  const main=[...document.querySelectorAll('.main-section[id]')],side=document.querySelector('.sidebar-card');
  const isMUJ=!!document.querySelector('a.logo[href="muj-jaipur.html"]');
  const mujLabels={
    profile:'University Profile',programmes:'Courses & Programmes',btech:'B.Tech',management:'Management',computing:'BCA & MCA',cost:'Fees & Cost',placements:'Placements',fit:'Who Should Choose MUJ?',faq:'FAQs',
    routes:'Admission Routes',documents:'Documents',selection:'Selection',fees:'Fee Check',eligibility:'Eligibility',admission:'Admission Routes',
    curriculum:'Curriculum',dual:'Dual Degree',career:'Career',comparison:'Programme Comparison',general:'General MBA',analytics:'Business Analytics',scholarship:'Scholarships',
    hons:'BBA Hons',imba:'Integrated MBA',choice:'Programme Choice',tracks:'BCA Tracks',mca:'MCA',bca:'BCA',numbers:'Placement Numbers',recruiters:'Recruiters',internships:'Internships',programme:'By Programme',roi:'ROI',
    hostel:'Hostel Setup',rooms:'Rooms & Food',facilities:'Facilities',rules:'Hostel Rules',decision:'Hostel Decision',mba:'MBA','mba-scholarship':'MBA Scholarships','ug-scholarship':'UG Scholarships'
  };
  if(side){
    const title=side.querySelector('.sidebar-title');side.innerHTML='';if(title)side.appendChild(title);
    main.forEach(s=>{const a=document.createElement('a');a.href='#'+s.id;const h=s.querySelector('h2');let label=h?h.textContent.replace(/\s+/g,' ').trim():s.id;if(isMUJ)label=mujLabels[s.id]||label.replace(/^MUJ\s+(Jaipur|Admission|B\.Tech|MBA|BBA|BCA\s*&\s*MCA|Placements|Fees|Campus\s*&\s*Hostel)\s*:?\s*/i,'').split(':')[0];a.textContent=label;side.appendChild(a)});
  }
  document.querySelectorAll('.faq-item h3').forEach(h=>h.addEventListener('click',()=>{const item=h.parentElement;document.querySelectorAll('.faq-item.open').forEach(x=>{if(x!==item)x.classList.remove('open')});item.classList.toggle('open')}));
  document.querySelectorAll('.mobile-on-page a').forEach(a=>a.addEventListener('click',()=>{const d=a.closest('details');if(d)d.removeAttribute('open')}));
  const links=[...document.querySelectorAll('.sidebar a')];
  const obs=new IntersectionObserver(es=>{es.forEach(e=>{const a=links.find(x=>x.getAttribute('href')==='#'+e.target.id);if(a&&e.isIntersecting){links.forEach(x=>x.classList.remove('active'));a.classList.add('active')}})},{rootMargin:'-20% 0px -70% 0px'});
  main.forEach(s=>obs.observe(s));
});
