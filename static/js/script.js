// const sideMenu = document.querySelector("aside");
// const menuBtn = document.querySelector("#menu-btn");
// const closeBtn = document.querySelector("#close-btn");
// const themeToggler = document.querySelector(".theme-toggler");

// // Show sidebar
// if (menuBtn && sideMenu) {
//   menuBtn.addEventListener("click", () => {
//     sideMenu.style.display = "block";
//   });
// }

// // Close sidebar
// if (closeBtn && sideMenu) {
//   closeBtn.addEventListener("click", () => {
//     sideMenu.style.display = "none";
//   });
// }

// // Change theme
// if (themeToggler) {
//   themeToggler.addEventListener("click", () => {
//     document.body.classList.toggle("dark-theme-variables");

//     const firstSpan = themeToggler.querySelector("span:nth-child(1)");
//     const secondSpan = themeToggler.querySelector("span:nth-child(2)");

//     if (firstSpan && secondSpan) {
//       firstSpan.classList.toggle("active");
//       secondSpan.classList.toggle("active");
//     }
//   });
// }

// // Ensure code runs after DOM is fully loaded
// document.addEventListener("DOMContentLoaded", function () {
//   const sidebarLinks = document.querySelectorAll(".sidebar a");
//   const defaultActiveLink = document.querySelector(".sidebar a:first-child");

//   let currentPath = window.location.pathname;
//   let activeLinkFound = false;

//   sidebarLinks.forEach((link) => {
//     const linkPath = new URL(link.href, window.location.origin).pathname;

//     if (linkPath !== "#" && linkPath === currentPath) {
//       link.classList.add("active");
//       activeLinkFound = true;
//     }
//   });

//   if (!activeLinkFound && defaultActiveLink) {
//     defaultActiveLink.classList.add("active");
//   }

//   sidebarLinks.forEach((link) => {
//     link.addEventListener("click", function () {
//       sidebarLinks.forEach((l) => l.classList.remove("active"));
//       this.classList.add("active");
//     });
//   });
// });

// // Dropdown Menu
// document.addEventListener("DOMContentLoaded", function () {
//   const dropdowns = document.querySelectorAll(".dropdown");

//   dropdowns.forEach(dropdown => {
//     const dropdownToggle = dropdown.querySelector(".dropdown-toggle");
//     const dropdownMenu = dropdown.querySelector(".dropdown-menu");
//     const dropdownLinks = dropdown.querySelectorAll(".dropdown-menu a");

//     // Check local storage for dropdown state
//     const storageKey = `dropdownOpen-${dropdown.querySelector("h3").textContent.trim()}`;
//     const isDropdownOpen = localStorage.getItem(storageKey) === "true";
//     if (isDropdownOpen) {
//       dropdownMenu.style.display = "block";
//     }

//     // Toggle dropdown visibility
//     dropdownToggle.addEventListener("click", function (e) {
//       e.preventDefault();
//       const isVisible = dropdownMenu.style.display === "block";
//       dropdownMenu.style.display = isVisible ? "none" : "block";
//       localStorage.setItem(storageKey, !isVisible);
//     });

//    // Replace the dropdownLinks forEach with this:
// dropdownLinks.forEach(link => {
//   link.addEventListener("click", function (e) {
//     // Special case for dashboard links
//     if (link.href.includes('dashboard')) {
//       // Let the default behavior happen
//       return true;
//     }
//     // For all other links
//     e.stopPropagation();
//   });
// });

//     // Close dropdown when clicking outside
//     document.addEventListener("click", function (e) {
//       // Check if clicked element is not part of any dropdown
//       const isInsideAnyDropdown = Array.from(dropdowns).some(drop => drop.contains(e.target));
//       if (!isInsideAnyDropdown) {
//         dropdowns.forEach(drop => {
//           drop.querySelector(".dropdown-menu").style.display = "none";
//           const key = `dropdownOpen-${drop.querySelector("h3").textContent.trim()}`;
//           localStorage.setItem(key, false);
//         });
//       }
//     });
//   });
// });
// // TABS

// function openTab(event, tabName) {
//   let i, tabcontent, tablinks;

//   tabcontent = document.getElementsByClassName("tab-content");
//   for (i = 0; i < tabcontent.length; i++) {
//     tabcontent[i].style.display = "none";
//   }

//   tablinks = document.getElementsByClassName("tab-button");
//   for (i = 0; i < tablinks.length; i++) {
//     tablinks[i].className = tablinks[i].className.replace(" active", "");
//   }

//   document.getElementById(tabName).style.display = "block";
//   event.currentTarget.className += " active";
// }

// // Show the first tab by default
// document.addEventListener("DOMContentLoaded", function () {
//   document.getElementsByClassName("tab-button")[0].click();
// });


// // Increase Sidebar with scroll 
// document.addEventListener("DOMContentLoaded", function () {
//   let sidebar = document.querySelector(".sidebar-div");
//   let initialHeight = sidebar.offsetHeight; // Get actual initial height
//   let maxHeight = window.innerHeight; // Use full viewport height
//   let scrollFactor = 3; // Adjust to control speed

//   window.addEventListener("scroll", function () {
//       let scrollY = window.scrollY;
//       let newHeight = initialHeight + (scrollY / scrollFactor);

//       if (newHeight > maxHeight) {
//           newHeight = maxHeight;
//       }

//       sidebar.style.height = newHeight + "px";
//   });
// });