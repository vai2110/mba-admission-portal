document.addEventListener('DOMContentLoaded',()=>{
  const labels={
    profile:'University Profile',programmes:'Courses & Programmes',btech:'B.Tech',management:'Management',computing:'BCA & MCA',cost:'Fees & Cost',placements:'Placements',fit:'Who Should Choose MUJ?',faq:'FAQs',
    routes:'Admission Routes',documents:'Documents',selection:'Selection',fees:'Fee Check',
    eligibility:'Eligibility',process:'Admission Process',timeline:'Important Dates',entrance:'Entrance Exams',
    cse:'CSE',branches:'Engineering Branches',curriculum:'Curriculum',dual:'Dual Degree',career:'Career Scope',
    mba:'MBA',analytics:'Business Analytics',integrated:'Integrated MBA',comparison:'Programme Comparison',
    bba:'BBA',bca:'BCA',mca:'MCA',tracks:'Specialisations',
    tuition:'Tuition Fees',hostel:'Hostel Fees',scholarships:'Scholarships',loans:'Education Loans',budget:'Total Cost',
    stats:'Placement Statistics',recruiters:'Recruiters',internships:'Internships',roles:'Roles & Careers',roi:'ROI Check',
    campus:'Campus',hostelinfo:'Hostel',facilities:'Facilities',studentlife:'Student Life',location:'Location'
  };
  const main=[...document.querySelectorAll('.main-section[id]')];
  const side=document.querySelector('.sidebar-card');
  if(side){
    const title=side.querySelector('.sidebar-title'); side.innerHTML=''; if(title) side.appendChild(title);
    main.forEach(s=>{const a=document.createElement('a');a.href='#'+s.id;const h=s.querySelector('h2');a.textContent=labels[s.id]||(h?h.textContent.replace(/\s+/g,' ').trim().replace(/^MUJ\s+(Jaipur|Admission)\s*:?\s*/i,'').split(':')[0]:s.id);side.appendChild(a)});
  }
  document.querySelectorAll('.faq-item h3').forEach(h=>h.addEventListener('click',()=>{const item=h.parentElement;document.querySelectorAll('.faq-item.open').forEach(x=>{if(x!==item)x.classList.remove('open')});item.classList.toggle('open')}));
  document.querySelectorAll('.mobile-on-page a').forEach(a=>a.addEventListener('click',()=>{const d=a.closest('details');if(d)d.removeAttribute('open')}));
  const links=[...document.querySelectorAll('.sidebar a')];
  const obs=new IntersectionObserver(es=>{es.forEach(e=>{const a=links.find(x=>x.getAttribute('href')==='#'+e.target.id);if(a&&e.isIntersecting){links.forEach(x=>x.classList.remove('active'));a.classList.add('active')}})},{rootMargin:'-20% 0px -70% 0px'});
  main.forEach(s=>obs.observe(s));
});
