/* CollegeDecoded AI advisor launcher is temporarily disabled site-wide.
   Keep this file in place so existing page script references remain safe.
   Re-enable the advisor only after an explicit product decision. */
(function () {
  "use strict";
  window.__collegeDecodedAdvisorLoaded = true;
  var existingRoot = document.getElementById("cd-advisor-root");
  if (existingRoot) existingRoot.remove();
})();
