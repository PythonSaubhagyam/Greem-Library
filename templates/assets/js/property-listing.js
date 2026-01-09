function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function togglePropertyField(propertyId, field, value) {
  fetch(`/properties/admin/${propertyId}/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    credentials: 'include',
    body: JSON.stringify({ [field]: value })
  })
    .then(res => {
      if (!res.ok) {
        throw new Error("Failed to update property");
      }
      return res.json();
    })
    .then(data => {
      // ✅ get current query params from URL
      const query = window.location.search; // e.g. ?is_imp=true&listing_type=Rent
      const baseUrl = "/properties/admin/";
      const fetchUrl = query ? `${baseUrl}${query}` : baseUrl;

      // ✅ now reload property list with same filters
      const path = window.location.pathname;
      
      if (path=="/admin-premium-properties/"){
        fetchProperties({is_premium:true}, fetchUrl);
      }
      else if (path=="/admin-imp-properties/"){
        fetchProperties({is_imp:true}, fetchUrl);
      }
      else{
        fetchProperties({}, fetchUrl);
      }

      showToast("Success", `Property marked successfully`, "success");
    })
    .catch(err => {
      console.error(`Error updating ${field} for property ${propertyId}:`, err);
      alert("Failed to update property. Please try again.");
    });
}

function toggleDropdown(event, rowId) {
  event.stopPropagation();

    // Close other dropdowns
    document.querySelectorAll(".aaaa").forEach(dd => dd.classList.remove("show"));
    document.querySelectorAll('tbody tr').forEach(row => row.style.zIndex = 1);
    document.querySelector(".tscroll")?.classList.remove("expand-table");

    const row = document.getElementById(rowId);
    const dropdown = row.querySelector('.aaaa');

    // Toggle this dropdown
    const isOpen = dropdown.classList.toggle('show');
    row.style.zIndex = isOpen ? 1000 : 1;

    if (isOpen) {
        const tscroll = document.querySelector(".tscroll");
        if (tscroll) {
            // Check current height in pixels
            const currentHeight = tscroll.offsetHeight;
            // Convert 135vh into pixels
            const expandHeight = window.innerHeight * 1.35;

            if (currentHeight < expandHeight) {
                tscroll.classList.add("expand-table");
            }
        }
    } else {
        document.querySelector(".tscroll")?.classList.remove("expand-table");
    }
}

document.addEventListener("click", function () {
    document.querySelectorAll(".aaaa").forEach(dd => dd.classList.remove("show"));
    document.querySelector(".tscroll")?.classList.remove("expand-table");
});

document.addEventListener("click", function (e) {
  if (e.target.classList.contains("show-contact")) {
    const btn = e.target;
    const propertyId = btn.dataset.propertyId;
    const isPremium = btn.dataset.isPremium === "true";
    const hasTwoContacts = btn.dataset.contact1 && btn.dataset.contact2;


    // 🟢 Non-premium: directly show contact info
    if (!isPremium) {
       btn.outerHTML = `
            <div style="
              background: #e9ecef;
              padding: 0px 10px 5px 10px;
              display: flex;
              justify-content: space-between;
              align-items: center;
              width: 100%;
            ">
              <!-- Name -->
              <div style="
              padding-top: 5px;
                font-weight: 500;
                color: #333;
                white-space: nowrap;
                flex-shrink: 0;
              ">
                ${btn.dataset.name || "-"}
              </div>

              <!-- Contact Numbers -->
              <div style="
                display: flex;
                flex-direction: ${btn.dataset.contact2 ? "column" : "row"};
                align-items: flex-end;
                gap: 4px;
                text-align: right;
                flex-shrink: 0;
              ">
                ${
                  btn.dataset.contact1
                    ? `<a href="tel:${btn.dataset.contact1}" 
                          style="display:inline-flex;align-items:center;gap:5px;
                                text-decoration:none;color:#007bff;font-size:14px;">
                          <i class="fa fa-phone" style="font-size:14px;color:#007bff;"></i>
                          ${btn.dataset.contact1}
                      </a>`
                    : ""
                }
                ${
                  btn.dataset.contact2
                    ? `<a href="tel:${btn.dataset.contact2}" 
                          style="display:inline-flex;align-items:center;gap:5px;
                                text-decoration:none;color:#007bff;font-size:14px;">
                          <i class="fa fa-phone" style="font-size:14px;color:#007bff;"></i>
                          ${btn.dataset.contact2}
                      </a>`
                    : ""
                }
              </div>
            </div>
          `;






      return;
    } 

    // 🟣 Premium: OTP Flow via SweetAlert2
    Swal.fire({
      title: "Enter OTP",
      html: `<p style="font-size:14px;">Sending OTP to admin email...</p>`,
      showCancelButton: true,
      showConfirmButton: false, // hide verify until OTP is sent
      confirmButtonText: "Verify OTP",
      width: window.innerWidth < 500 ? "90%" : "400px",
      allowOutsideClick: false,
      didOpen: () => {
        // 🔹 Step 1: Call API to send OTP
        fetch("/api/generate-otp/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({ property_id: propertyId }),
        })
          .then(async (res) => {
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || data.message || "Failed to send OTP");

            // 🔹 Step 2: Clean entire SweetAlert content before re-render
            const swalContainer = Swal.getHtmlContainer();
            if (swalContainer) swalContainer.innerHTML = "";

            // 🔹 Step 3: Rebuild the inner HTML cleanly (no duplication)
            Swal.update({
              html: `
                <p style="font-size:14px;">OTP has been sent to admin email.</p>
                <input id="otp-input" class="swal2-input" placeholder="Enter 6-digit OTP"
                       maxlength="6" inputmode="numeric" pattern="[0-9]*" />
              `,
              showConfirmButton: true,
            });
          })
          .catch((err) => {
            Swal.update({
              html: `<p style="color:red">${err.message}</p>`,
            });
          });
      },
      preConfirm: () => {
        const otp = document.getElementById("otp-input")?.value.trim();
        if (!otp) {
          Swal.showValidationMessage("Please enter OTP");
          return false;
        }
        return otp;
      },
    }).then((result) => {
      if (result.isConfirmed) {
        // 🔹 Step 4: Verify OTP
        fetch("/api/verify-otp/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
          },
          body: JSON.stringify({ property_id: propertyId, otp: result.value }),
        })
          .then(async (res) => {
            const verifyData = await res.json();
            if (!res.ok) throw new Error(verifyData.error || verifyData.message || "Invalid OTP");

            Swal.fire({
              icon: "success",
              title: "Verified",
              text: verifyData.message,
              timer: 1500,
              showConfirmButton: false,
            });

            // ✅ Reveal contact info
           btn.outerHTML = `
            <div style="
              background: #e9ecef;
              padding: 0px 10px 5px 10px;
              display: flex;
              justify-content: space-between;
              align-items: center;
              width: 100%;
            ">
              <!-- Name -->
              <div style="
                padding-top: 5px;
                font-weight: 500;
                color: #333;
                white-space: nowrap;
                flex-shrink: 0;
              ">
                ${btn.dataset.name || "-"}
              </div>

              <!-- Contact Numbers -->
              <div style="
                display: flex;
                flex-direction: ${btn.dataset.contact2 ? "column" : "row"};
                align-items: flex-end;
                gap: 4px;
                text-align: right;
                flex-shrink: 0;
              ">
                ${
                  btn.dataset.contact1
                    ? `<a href="tel:${btn.dataset.contact1}" 
                          style="display:inline-flex;align-items:center;gap:5px;
                                text-decoration:none;color:#007bff;font-size:14px;">
                          <i class="fa fa-phone" style="font-size:14px;color:#007bff;"></i>
                          ${btn.dataset.contact1}
                      </a>`
                    : ""
                }
                ${
                  btn.dataset.contact2
                    ? `<a href="tel:${btn.dataset.contact2}" 
                          style="display:inline-flex;align-items:center;gap:5px;
                                text-decoration:none;color:#007bff;font-size:14px;">
                          <i class="fa fa-phone" style="font-size:14px;color:#007bff;"></i>
                          ${btn.dataset.contact2}
                      </a>`
                    : ""
                }
              </div>
            </div>
          `;



          })
          .catch((err) => {
            Swal.fire("Error", err.message, "error");
          });
      }
    });
  }
});





function updateQueryParam(key, value) {
    const url = new URL(window.location);
    url.searchParams.set(key, value);
    window.history.pushState({}, "", url);
}

function renderPagination(totalPages, currentPage) {
    const pagination = document.querySelector(".pagination");
    pagination.innerHTML = "";
    const isMobile = window.innerWidth <= 790;

    function addPageItem(page, label = null, active = false, disabled = false) {
        const li = document.createElement("li");
        li.className = `page-item ${active ? "active" : ""} ${disabled ? "disabled" : ""}`;
        const a = document.createElement("a");
        a.className = "page-link";
        a.href = "javascript:void(0);";
        a.innerHTML = label || page;
        if (!disabled && !active) {
            a.addEventListener("click", () => {
                // Get current query params
                const params = new URLSearchParams(window.location.search);

                // Preserve all existing keys but update page
                params.set("page", page);

                // Optional: Update the URL in browser
                window.history.pushState({}, "", `${window.location.pathname}?${params.toString()}`);

                // Call fetchProperties with all params as an object
                const filters = {};
                for (const [key, value] of params.entries()) {
                    // Convert comma-separated values back to arrays if needed
                    if (value.includes(",")) {
                        filters[key] = value.split(",");
                    } else {
                        filters[key] = value;
                    }
                }

                fetchProperties(filters);
            });
        }
        li.appendChild(a);
        pagination.appendChild(li);
    }

    // First & Prev
    addPageItem(1, `<i class="tf-icon bx bx-chevrons-left bx-sm"></i>`, false, currentPage === 1);
    if (currentPage > 1) {
        addPageItem(currentPage - 1, `<i class="tf-icon bx bx-chevron-left bx-sm"></i>`);
    } else {
        addPageItem(1, `<i class="tf-icon bx bx-chevron-left bx-sm"></i>`, false, true);
    }

    // Page range
    if (isMobile) {
      let start = Math.max(1, currentPage - 1);
      let end = Math.min(totalPages, currentPage + 1);

      // Adjust if at the start or end
      if (currentPage === 1) end = Math.min(totalPages, 3);
      if (currentPage === totalPages) start = Math.max(1, totalPages - 2);

      for (let p = start; p <= end; p++) {
          addPageItem(p, p, p === currentPage);
      }
    } else {
      let maxVisible = 5; // total visible numbers
      let start = Math.max(1, currentPage - 2);
      let end = Math.min(totalPages, currentPage + 2);

      // Adjust range if near start or end
      if (currentPage <= 3) {
          end = Math.min(totalPages, maxVisible);
      }
      if (currentPage >= totalPages - 2) {
          start = Math.max(1, totalPages - (maxVisible - 1));
      }

      for (let p = start; p <= end; p++) {
          addPageItem(p, p, p === currentPage);
      }
    }
    // Next & Last
    if (currentPage < totalPages) {
        addPageItem(currentPage + 1, `<i class="tf-icon bx bx-chevron-right bx-sm"></i>`);
    } else {
        addPageItem(totalPages, `<i class="tf-icon bx bx-chevron-right bx-sm"></i>`, false, true);
    }
    addPageItem(totalPages, `<i class="tf-icon bx bx-chevrons-right bx-sm"></i>`, false, currentPage === totalPages);
}


function fetchProperties(filters = {}, baseUrl = "/properties/admin/") {
  const tbody = document.getElementById('property-table-body1');
  const cardContainer = document.getElementById("property-card-container");
  if (!tbody) return; // avoid error if table not on page
  const isMobile = window.innerWidth <= 480;
  
  if (isMobile && cardContainer) {
    cardContainer.innerHTML = `
      <div class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    `;
  } else {
  tbody.innerHTML = `
    <tr id="property-loader-row">
      <td colspan="16" class="text-center py-5">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </td>
    </tr>
  `;
  }

  // const queryString = new URLSearchParams(filters).toString();
  const queryParams = [];
  for (const [key, value] of Object.entries(filters)) {
    if (Array.isArray(value)) {
      if (value.length > 0) {
        value.forEach(v => queryParams.push(`${encodeURIComponent(key)}=${encodeURIComponent(v)}`));
      }
    } else if (value !== '' && value !== null && value !== undefined) {
      queryParams.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
    }
  }
  const queryString = queryParams.join('&');
  const url = queryString ? `${baseUrl}?${queryString}` : baseUrl;

  fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    credentials: 'include'
  })
    .then(res => res.json())
    .then(data => {
      console.log(data,'-------------')
      const results = data.results || data; // array of properties
      console.log(results,'-------------')
      tbody.innerHTML = "";
      if (isMobile && cardContainer) cardContainer.innerHTML = ""; // clear spinner before adding cards


      const params = new URLSearchParams(window.location.search);
      const currentPage = parseInt(params.get("page") || "1", 10);
      const startIndex = (currentPage - 1) * data.rows_per_page;


      const tableHead = document.querySelector("table thead");
      if (isMobile) {
        if (tableHead) tableHead.style.display = "none";
      } else {
        if (tableHead) tableHead.style.display = "";
      }

      if (!results.length) {
        const noData = `<div class="text-center py-4">No properties found</div>`;
        if (isMobile && cardContainer) cardContainer.innerHTML = noData;
        else tbody.innerHTML = `<tr><td colspan="15" class="text-center">No properties found</td></tr>`;
        return;
      }

      results.forEach((property, index) => {
       const whatsappMessage = encodeURIComponent(
        `Hello ,\n\n` +
        `I am reaching out regarding property "${property.title || ''}" located at ${property.address || ''}.\n` +
        `Type: ${property.listing_type || '-'}\n` +
        `Price: ${property.price || '-'}\n` +
        `Area: ${property.area_sqft || '-'}\n` +
        `Status: ${property.status || '-'}\n\n` +
        `Please let me know if you are available to discuss.`
      );

      const whatsappUrl = `https://wa.me/91${property.contact_number || ''}`;
      const whatsappShareUrl = `https://api.whatsapp.com/send?text=${whatsappMessage}`;

        const row = `
          <tr id="row-${index}">
            <td><span class="badge bg-label-primary">${startIndex + index + 1}</span></td>
            <td>${property.title || '-'}</td>
            <td>${property.listing_type || '-'}</td>
            <td>
              ${new Date(property.created_at).toLocaleString('en-US', {
                year: 'numeric',
                month: 'short',
                day: '2-digit',
                hour: 'numeric',
                minute: '2-digit',
                hour12: true,
              })}
            </td>
            <td>
              <button class="btn btn-sm btn-primary show-contact"
                data-property-id="${property.id}"
                data-name="${property.contact_name || '-'}"
                data-contact1="${property.contact_number || ''}"
                data-contact2="${property.contact_number2 || ''}"
                data-is-premium="${property.is_premium}">
                Show Contact Info
              </button>
            </td>
            <td style="white-space: normal; word-wrap: break-word;">${property.address || '-'}</td>
            <td>${property.premise_name || '-'}</td>
            <td>${property.area_name || '-'}</td>
            <td>${property.price ? '₹ ' + property.price : '-'}</td>
            <td>${property.property_availability_type || '-'}</td>
            <td>${property.furnished_status || '-'}</td>
            <td>${property.property_age || '-'}</td>
            <td>
              ${property.description || ''} 
              ${property.description && property.special_note ? ' - ' : ''}
              ${property.special_note || ''}
              ${!property.description && !property.special_note ? '-' : ''}
            </td>
            <td>
              ${property.furnished_status || ''} 
              ${property.furnished_status && property.other_details ? ' - ' : ''}
              ${property.other_details || ''}
              ${!property.furnished_status && !property.other_details ? '-' : ''}
            </td>
            <td>
            ${
              property.area_sqft && property.measurement_name
                ? property.area_sqft + ' ' + property.measurement_name
                : property.area_sqft
                  ? property.area_sqft
                  : property.measurement_name || '-'
            }
          </td>

            <td style="white-space: normal; word-wrap: break-word;">${property.key_status || '-'} 
                ${property.key_call_before_hours ? `(Call before ${property.key_call_before_hours}h)` : ''}</td>
            <td>${property.brokerage_info || '-'}</td>
            <td>
              <span class="badge"
                    style="background-color:${property.status === 'Available' ? '#008000' : '#6c757d'};">
                ${property.status}
              </span>
            </td>
            <td>${property.rented_out 
                  ? '<span class="badge bg-danger">Yes</span>' 
                  : '<span class="badge" style="background-color:#008000;">No</span>'}</td>
            <td>
              <div class="d-flex flex-wrap justify-content-between align-items-center mt-3 gap-2">
                <div class="dropdown ${isMobile ? '' : 'aaaa'}">
                  ${isMobile
                    ? `<button type="button" class="btn p-0 dropdown-toggle hide-arrow" data-bs-toggle="dropdown">
                        <i class="bx bx-dots-vertical-rounded"></i>
                      </button>`
                    : `<button type="button" class="btn p-0 dropdown-toggle hide-arrow" onclick="toggleDropdown(event, 'row-${index}')">
                        <i class="bx bx-dots-vertical-rounded"></i>
                      </button>`
                  }
                  <div class="dropdown-menu ${isMobile ? '' : 'bbb'}">
                    <a class="dropdown-item text-info" href="/admin-properties/edit/${property.id}/">
                      <i class="bx bx-edit-alt me-1"></i> Edit
                    </a>
                    <a class="dropdown-item text-danger" href="javascript:void(0);" onclick="deleteProperty(${property.id})">
                      <i class="bx bx-trash me-1"></i> Delete
                    </a>
                    <a class="dropdown-item text-success" target="_blank" href="${whatsappShareUrl}">
                      <i class="bx bxl-whatsapp me-1"></i> Share
                    </a>
                  </div>
                  <i class="menu-icon tf-icons bx ${property.is_premium ? "bxs-crown text-warning" : "bx-crown text-secondary"} ${isMobile ? "ms-2" : ""}"
                    style="cursor:pointer"
                    title="Toggle Premium"
                    onclick="togglePropertyField(${property.id}, 'is_premium', ${!property.is_premium})">
                  </i>

                  <i class="menu-icon tf-icons bx ${property.is_imp ? "bxs-bookmark text-warning" : "bx-bookmark text-secondary"}"
                    style="cursor:pointer"
                    title="Toggle Important"
                    onclick="togglePropertyField(${property.id}, 'is_imp', ${!property.is_imp})">
                  </i>

                  ${property.contact_number
                    ? `
                      <a target="_blank" href="${whatsappUrl}">
                        <i class="bx bxl-whatsapp" style="color: #25D366; font-size: 22px; cursor: pointer;"></i>
                      </a>
                    `
                    : `
                      <i class="bx bxl-whatsapp text-muted" 
                        style="font-size: 22px; opacity: 0.5; cursor: not-allowed;"
                        title="WhatsApp unavailable - no contact number"></i>
                    `
                  }
                </div>
              </div>
            </td>
          </tr>
        `;
// #007b83;color:#fff
      const cardHTML = `
        <div class="property-card mb-3 shadow-sm rounded border" 
            style="border-color:#d9d9d9;background:#fff;overflow:hidden;">
          
          <!-- 🔹 Blue Header -->
          <div class="px-2 py-2 d-flex justify-content-between align-items-center" 
              style="background:#5F61E6;border-top-left-radius:8px;border-top-right-radius:8px;">
            
            <h6 class="mb-0 fw-bold" 
                style="color:#fff;font-size:15px;max-width:65%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
              ${property.premise_name || '-'}
            </h6>

            <div class="d-flex align-items-center" style="gap:8px;flex-shrink:0;">
              <i class="bx ${property.is_premium ? 'bxs-crown text-warning' : 'bx-crown text-white'}"
                style="cursor:pointer;font-size:18px;"
                title="Toggle Premium"
                onclick="togglePropertyField(${property.id}, 'is_premium', ${!property.is_premium})"></i>

              <i class="bx ${property.is_imp ? 'bxs-bookmark text-warning' : 'bx-bookmark text-white'}"
                style="cursor:pointer;font-size:18px;"
                title="Toggle Important"
                onclick="togglePropertyField(${property.id}, 'is_imp', ${!property.is_imp})"></i>

              ${
                property.contact_number
                  ? `<a target="_blank" href="${whatsappUrl}" title="Message on WhatsApp">
                      <i class="bx bxl-whatsapp" style="color:#25D366;font-size:20px;cursor:pointer;"></i>
                    </a>`
                  : `<i class="bx bxl-whatsapp text-muted"
                      style="font-size:20px;opacity:0.5;cursor:not-allowed;"
                      title="WhatsApp unavailable"></i>`
              }
            </div>
          </div>

          <!-- 🔹 Body -->
          <div class="p-2">
            <p class="fw-semibold mb-1 text-dark" style="font-size:14px;">
              ${property.listing_type || '-'} 
              <span class="float-end text-dark fw-bold" style="font-size:14px;">₹ ${property.price || '-'} Thd</span>
            </p>

            <p class="mb-1 fw-bold" style="font-size:13px;">${property.property_availability_type || '-'}</p>
            <p class="mb-1 fw-bold" style="font-size:13px;">${property.furnished_status || '-'}</p>

            <p class="mb-1" style="font-size:13px;">
              <strong>Sqft:</strong> ${property.area_sqft || '-'}
              <span class="float-end"><strong>Brokerage:</strong> ${property.brokerage_info || 'No Brokerage'}</span>
            </p>

            <p class="mb-1" style="font-size:13px;"><i class="bx bx-map-pin"></i> ${property.address}</p>

            <p class="mb-2" style="font-size:13px;">
              <strong>Property Status:</strong> 
              <span class="text-${property.status === 'Available' ? 'success' : 'secondary'} fw-semibold">
                ${property.status || '-'}
              </span>
            </p>

            <!-- 🔹 Rent Out + Show More -->
            <div class="d-flex justify-content-between align-items-center mb-2" style="gap:10px;flex-wrap:wrap;">
              <div class="form-check mb-0" style="font-size:13px;">
                <input type="checkbox" class="form-check-input rent-out-toggle" id="rentOut-${property.id}" 
                      ${property.rented_out ? 'checked' : ''} 
                      onclick="togglePropertyField(${property.id}, 'rented_out', this.checked)">
                <label class="form-check-label" for="rentOut-${property.id}" style="font-size:13px;">Click To Rent Out</label>
              </div>

              <button class="btn btn-link p-0 text-primary show-more-btn"
                      type="button"
                      data-bs-toggle="collapse"
                      data-bs-target="#details-${index}"
                      aria-expanded="false"
                      aria-controls="details-${index}"
                      style="font-size:13px;text-decoration:none;">
                Show More
              </button>
            </div>

            <!-- 🔹 Collapsible Section -->
            <div class="collapse" id="details-${index}">
              <div class="p-2 bg-light rounded mt-1">
                <p class="mb-1" style="font-size:13px;"><strong>Description:</strong> ${property.other_details || '-'}</p>
                <p class="mb-1" style="font-size:13px;"><strong>Key Status:</strong> ${property.key_status || '-'}</p>
                <p class="mb-1" style="font-size:13px;"><strong>Special Note:</strong> ${property.special_note || '-'}</p>
                <p class="mb-0" style="font-size:13px;"><strong>Call Before:</strong> ${property.key_call_before_hours ? property.key_call_before_hours + ' hrs' : '-'}</p>

                <div class="d-flex flex-wrap justify-content-between align-items-center mt-3" style="gap:6px;">
                  <a href="/admin-properties/edit/${property.id}/" 
                    class="btn btn-sm btn-outline-info flex-grow-1 text-nowrap" style="font-size:13px;">
                    <i class="bx bx-edit-alt"></i> Edit
                  </a>
                  <a target="_blank" href="${whatsappShareUrl}" 
                    class="btn btn-sm btn-outline-success flex-grow-1 text-nowrap" style="font-size:13px;">
                    <i class="bx bxl-whatsapp"></i> Share
                  </a>
                  <button class="btn btn-sm btn-outline-danger flex-grow-1 text-nowrap" 
                          onclick="deleteProperty(${property.id})" style="font-size:13px;">
                    <i class="bx bx-trash"></i> Delete
                  </button>
                </div>
              </div>
            </div>

            <!-- 🔹 Contact Info Button -->
            <div style="
              border-top: 1px solid #d0d0d0;
              background: #e9ecef;
              padding: 0px 10px 5px 10px;
              display: flex;
              justify-content: space-between;
              align-items: center;
              width: 100%;
            ">
            <button class="btn btn-sm btn-outline-primary w-100 mt-2 show-contact"
              data-name="${property.contact_name || '-'}"
              data-contact1="${property.contact_number || ''}"
              data-contact2="${property.contact_number2 || ''}"
              data-property-id="${property.id}"
              data-is-premium="${property.is_premium}"
              style="font-size:13px;">
              Get Contact Info
            </button>
            </div>
          </div>
        </div>
      `;





        document.addEventListener("click", function(e){
        if(e.target.closest("[data-bs-toggle='collapse']")){
          const btn = e.target.closest("[data-bs-toggle='collapse']");
          const target = document.querySelector(btn.getAttribute("data-bs-target"));
          const showText = btn.querySelector(".show-text");
          const hideText = btn.querySelector(".hide-text");

          target.addEventListener("shown.bs.collapse", ()=>{ 
            showText.classList.add("d-none");
            hideText.classList.remove("d-none");
          });
          target.addEventListener("hidden.bs.collapse", ()=>{ 
            showText.classList.remove("d-none");
            hideText.classList.add("d-none");
          });
        }
      });


        if (isMobile && cardContainer) cardContainer.insertAdjacentHTML("beforeend", cardHTML);
        else tbody.insertAdjacentHTML("beforeend", row);
      });

      if (!isMobile) {tbody.insertAdjacentHTML("beforeend", `
        <tr>
          <td colspan="19"></td>
          <td class="text-end fw-bold text-primary aaaa">
            Total Records: ${data.count}
          </td>
        </tr>
      `);
      }

      if (data.total_pages) {
        const pagination_div = document.querySelector(".demo-inline-spacing");
        if (pagination_div) {
          pagination_div.classList.remove("d-none");
        }
        renderPagination(data.total_pages, data.current_page);
      }
    })
    .catch(err => {
      const errHTML = `<div class="text-danger text-center py-4">Error fetching data</div>`;
      if (isMobile && cardContainer) cardContainer.innerHTML = errHTML;
      else tbody.innerHTML = `<tr><td colspan="19" class="text-danger text-center">Error fetching data</td></tr>`;
      console.error("Error fetching properties:", err);
    });
}


function showToast(title, message, status = "primary") {
    const toast = document.getElementById("alert-box");
    const toastTitle = document.getElementById("toast-title");
    const toastBody = document.getElementById("toast-body");
    const toastIcon = document.getElementById("toast-icon");

    toast.className = `bs-toast toast bg-${status} toast-placement-ex top-0 end-0 m-2 show`;
    toastTitle.textContent = title;
    toastBody.textContent = message;

    toastIcon.className = `bx me-2 ${status === "success" ? "bx-check-circle" : "bx-error"}`;

    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

let propertyToDelete = null;
const deleteModalEl = document.getElementById('deleteConfirmModal');
let deleteModal = null;
if (deleteModalEl) deleteModal = new bootstrap.Modal(deleteModalEl);

function deleteProperty(id) {
  propertyToDelete = id;
  deleteModal.show(); // reuse the same modal instance
}

document.addEventListener("DOMContentLoaded", () => {

  const applyBtn = document.getElementById('applyFiltersBtn');

  // const offcanvasElement = document.getElementById('offcanvasEnd');
  // const bsOffcanvas = new bootstrap.Offcanvas(offcanvasElement);

  // bsOffcanvas.show();

  applyBtn?.addEventListener('click', () => {
    const filters = {
      propertyType: document.getElementById('filterPropertyType')?.value,
      premium: document.getElementById('filterPremium')?.value,
      condition: document.getElementById('filterCondition')?.value,
      area: Array.from(document.getElementById('filterArea')?.selectedOptions || []).map(opt => opt.value),
      availability: document.getElementById('filterAvailability')?.value,
      availabilityType: document.getElementById('filterAvailabilityType')?.value,
      descriptionTags: Array.from(document.getElementById('filterDescriptionTags')?.selectedOptions || []).map(opt => opt.value),
      budgetMin: document.getElementById('filterBudgetMin')?.value,
      budgetMax: document.getElementById('filterBudgetMax')?.value,
      sqftMin: document.getElementById('filterSqftMin')?.value,
      sqftMax: document.getElementById('filterSqftMax')?.value,
      contactPremise: document.getElementById('filterContactPremise')?.value
    };

    console.log('Filters Applied:', filters);

    // TODO: Apply filters to your table (AJAX or JS filtering)
  });


  fetch('/api/get-areas/')  // replace with your API endpoint
    .then(res => res.json())
    .then(data => {
      const areaSelect = document.getElementById('filterArea');
      areaSelect.innerHTML = ''; // clear existing options

      // Filter out null, undefined, or empty strings
      const validAreas = data.areas.filter(area => area && area.trim() !== '');

      validAreas.forEach(area => {
        const option = document.createElement('option');
        option.value = area;
        option.textContent = area;
        areaSelect.appendChild(option);
      });
    })
    .catch(err => console.error('Error fetching areas:', err));

  // document.getElementById('applyFiltersBtn').addEventListener('click', () => {
  //   const params = new URLSearchParams();

  //   if (window.location.pathname.includes('/admin-imp-properties/')) {
  //       params.append('is_imp', true);
  //   } else if (window.location.pathname.includes('/admin-premium-properties/')) {
  //       params.append('is_premium', true);
  //   }

  //   const propertyType = document.getElementById('filterPropertyType').value;
  //   console.log(propertyType,'---------')
  //   if (propertyType) params.append('listing_type', propertyType);

  //   // const premium = document.getElementById('filterPremium').value;
  //   // if (premium) params.append('is_premium', premium);

  //   const condition = document.getElementById('filterCondition').value;
  //   if (condition) params.append('condition', condition);

  //   const areaSelect = document.getElementById('filterArea');
  //   const areas = Array.from(areaSelect.selectedOptions).map(o => o.value);
  //   if (areas.length) areas.forEach(a => params.append('area', a));

  //   // const availability = document.getElementById('filterAvailability').value;
  //   // if (availability) params.append('availability', availability);

  //   const premiumCheck = document.getElementById('filterPremiumCheck').checked;
  //   if (premiumCheck) params.append('is_premium', true);

  //   const availabilityType = document.getElementById('filterAvailabilityType').value;
  //   if (availabilityType) params.append('availability_type', availabilityType);

  //   // const descriptionSelect = document.getElementById('filterDescriptionTags');
  //   // const tags = Array.from(descriptionSelect.selectedOptions).map(o => o.value);
  //   // if (tags.length) tags.forEach(t => params.append('description_tags', t));

  //   const budgetMin = document.getElementById('filterBudgetMin').value;
  //   const budgetMax = document.getElementById('filterBudgetMax').value;
  //   if (budgetMin) params.append('budget_min', budgetMin);
  //   if (budgetMax) params.append('budget_max', budgetMax);

  //   const sqftMin = document.getElementById('filterSqftMin').value;
  //   const sqftMax = document.getElementById('filterSqftMax').value;
  //   if (sqftMin) params.append('sqft_min', sqftMin);
  //   if (sqftMax) params.append('sqft_max', sqftMax);

  //   const search = document.getElementById('filterContactPremise').value;
  //   if (search) params.append('search', search);
    
  //    fetchProperties(params);

  //   //  bsOffcanvas.hide(); // close modal after filter
    
  // });


  document.querySelectorAll('.dropdown-toggle').forEach(btn => {
    btn.addEventListener('click', function(e) {
      const dropdown = this.nextElementSibling; // the menu
      const rect = this.getBoundingClientRect();
      dropdown.style.top = `${rect.bottom}px`;
      dropdown.style.left = `${rect.left}px`;
    });
  });

 const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener("click", function() {
      if (!propertyToDelete) return;

      fetch(`/properties/admin/${propertyToDelete}/`, {
        method: "DELETE",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
      })
        .then((res) => {
          if (res.ok) {
            showToast("Success", "Property deleted", "success");
            fetchProperties();
            deleteModal.hide();
          } else {
            showToast("Error", "Failed to delete property", "danger");
          }
        })
        .catch(() => showToast("Error", "Something went wrong", "danger"));
    });
  }
});