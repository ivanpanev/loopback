<!DOCTYPE html>
<html>
<head>
  <title>Firewall Object Config Generator - Extended</title>
  <!-- Font Awesome for icons -->
  <link rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.0/css/all.min.css"
    integrity="sha512-..."
    crossorigin="anonymous" referrerpolicy="no-referrer" />
  <style>
    /* ===== FONT & COLOR PALETTE ===== */
    @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600&display=swap');

    :root {
      --primary-color: #3B5BA9; /* deep subdued blue */
      --primary-color-hover: #2D4986;
      --background-color: #f3f5f9; /* light background gray/blue */
      --text-color: #333;         /* typical text color */
      --header-bg: #ffffff;       /* container background */
      --header-text-color: #444;
      --error-color: #fee2e2;
      --error-border: #fecaca;
      --warning-color: #fff8ce;
      --warning-border: #f9ee96;
      --success-color: #e6ffe6;
      --success-border: #b2e2b2;
      --success-text: #265f26;
      --invalid-row-bg: #ffe6e6;
      --warning-row-bg: #fff8ce;
      --highlight-bg: #e1ffda; /* pale green for fill-drag highlight */
      --table-header-bg: #e9edf2;
      --table-border-color: #d0d7de;
      --table-row-hover: #f6f8fa;
    }

    /* ===== GLOBAL STYLES ===== */
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    body {
      font-family: 'Open Sans', sans-serif;
      background-color: var(--background-color);
      color: var(--text-color);
      line-height: 1.4;
      position: relative; /* for toast positioning */
    }
    .container {
      max-width: 1300px;
      margin: 1rem auto;
      padding: 1.5rem;
      background-color: var(--header-bg);
      border-radius: 6px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }

    /* ===== HEADINGS ===== */
    h1, h2 {
      color: var(--header-text-color);
      font-weight: 600;
      margin-bottom: 0.75rem;
    }

    /* ===== CONTROL BAR & COLUMNS ===== */
    .control-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1rem;
    }
    .col {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      min-width: 120px; /* just to help keep columns distinct */
    }

    /* For horizontal button grouping (two in a column) */
    .col > .button-group {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    /* ===== BUTTONS & CHECKBOX ===== */
    .button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 4px; /* space between icon & text */
      padding: 6px 12px;
      border-radius: 4px;
      border: none;
      background: var(--primary-color);
      color: #fff;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s, transform 0.2s;
      font-size: 0.875rem;
    }
    .button:hover {
      background: var(--primary-color-hover);
      transform: translateY(-1px);
    }
    .button.delete-btn {
      background: #d64545;
    }
    .button.delete-btn:hover {
      background: #bb3b3b;
    }

    label {
      display: flex;
      align-items: center;
      gap: 0.3rem;
      cursor: pointer;
      font-size: 0.875rem;
      font-weight: 600;
    }

    /* ===== VENDOR SELECTOR ===== */
    .vendor-selector {
      position: relative;
      display: inline-block;
    }
    .vendor-selection-button {
      display: flex;
      align-items: center;
      gap: 8px;
      border: 1px solid #ccc;
      padding: 8px 12px;
      border-radius: 6px;
      background: white;
      cursor: pointer;
      user-select: none;
      font-weight: 500;
      min-width: 150px;
    }
    .vendor-selection-button img {
      width: 20px;
      height: 20px;
    }
    .vendor-options {
      position: absolute;
      top: 100%;
      left: 0;
      background: white;
      border: 1px solid #ccc;
      border-radius: 6px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
      overflow: hidden;
      z-index: 1000;
      display: none; /* toggled via JS */
      width: 240px;
    }
    .vendor-option {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      cursor: pointer;
    }
    .vendor-option:hover {
      background-color: #f3f6f9;
    }
    .vendor-option img {
      width: 20px;
      height: 20px;
    }
    .vendor-option span {
      white-space: nowrap;
    }

    /* ===== TABLE STYLES ===== */
    .excel-table {
      width: 100%;
      border-collapse: collapse;
      border: 1px solid var(--table-border-color);
      background-color: #fff;
      table-layout: fixed; /* fixed layout for column resizing */
    }
    .excel-table thead th {
      background: var(--table-header-bg);
      color: #555;
      font-weight: 600;
      font-size: 0.875rem;
      border: 1px solid var(--table-border-color);
      padding: 8px;
      text-align: left;
      position: relative; /* for the resize handle */
      min-width: 50px;
    }
    .col-resize-handle {
      position: absolute;
      right: 0;
      top: 0;
      width: 6px;
      height: 100%;
      cursor: col-resize;
      user-select: none;
      z-index: 5;
    }
    .excel-table tbody tr:nth-of-type(even) {
      background-color: #fafbfc; /* subtle row striping */
    }
    .excel-table th.idx-col { width: 40px; text-align: center; }
    .excel-table th.actions-col { width: 60px; text-align: center; }

    .excel-table td {
      border: 1px solid var(--table-border-color);
      vertical-align: middle;
      padding: 0;
      font-size: 0.875rem;
      overflow: hidden; /* ensures text doesn't overflow */
      position: relative; /* for absolutely positioned .drag-handle */
    }
    .excel-table tbody tr:hover {
      background-color: var(--table-row-hover);
    }
    .excel-table input[type="text"] {
      width: 100%;
      height: 100%;
      border: none;
      background-color: transparent;
      padding: 6px 8px;
      font-size: 0.875rem;
      outline: none;
    }
    .excel-table input[type="text"]:focus {
      outline: 1px dotted var(--primary-color);
      background-color: #fff;
    }
    .drag-handle {
      position: absolute;
      bottom: 3px;
      right: 3px;
      width: 8px;
      height: 8px;
      background: #888;
      cursor: crosshair;
      border: 1px solid #555;
      box-shadow: inset -1px -1px 0 0 #aaa;
      z-index: 10;
    }
    .drag-handle:hover {
      content: attr(title);
    }

    /* ===== ERROR / WARNING / SUCCESS FEEDBACK ===== */
    .error-block,
    .warning-block,
    .success-block {
      border: 1px solid;
      padding: 0.75rem 1rem;
      border-radius: 4px;
      margin-bottom: 1rem;
      font-size: 0.9rem;
    }
    .error-block {
      background: var(--error-color);
      border-color: var(--error-border);
      color: #b91c1c;
      font-weight: 500;
    }
    .warning-block {
      background: var(--warning-color);
      border-color: var(--warning-border);
      color: #856404;
      font-weight: 500;
    }
    .success-block {
      background: var(--success-color);
      border-color: var(--success-border);
      color: var(--success-text);
      font-weight: 500;
    }
    .invalid-row {
      background-color: var(--invalid-row-bg) !important;
    }
    .warning-row {
      background-color: var(--warning-row-bg) !important;
    }
    .drag-highlight {
      background-color: var(--highlight-bg) !important;
    }
    .group-separator {
      border-bottom: 3px double #666 !important;
    }

    /* ===== CLI OUTPUT & COPY BUTTON ===== */
    .cli-output {
      background: #2f2f2f;
      color: #cbd5e0;
      padding: 1rem;
      border-radius: 4px;
      font-family: Consolas, monospace;
      font-size: 0.875rem;
      white-space: pre-wrap;
      margin-top: 1rem;
    }
    .cli-output-container {
      position: relative;
      margin-top: 1rem;
    }
    .copy-button {
      display: none;
      position: absolute;
      top: 8px;
      right: 8px;
      background: #666;
      color: #fff;
      border: none;
      border-radius: 3px;
      padding: 4px 8px;
      cursor: pointer;
      font-size: 0.75rem;
      opacity: 0.8;
    }
    .cli-output-container:hover .copy-button {
      display: block;
    }
    .copy-button:hover {
      opacity: 1.0;
    }

    /* Toast notification */
    .toast {
      position: fixed;
      top: 16px;
      right: 16px;
      background: #333;
      color: #fff;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 0.9rem;
      z-index: 9999;
      opacity: 0.95;
      box-shadow: 0 2px 6px rgba(0,0,0,0.2);
      animation: fadeInOut 2.5s forwards;
    }
    @keyframes fadeInOut {
      0%   { opacity: 0;   transform: translateY(-10px); }
      10%  { opacity: 0.95;transform: translateY(0); }
      80%  { opacity: 0.95;transform: translateY(0); }
      100% { opacity: 0;   transform: translateY(-10px); }
    }

    /* ===== MODAL DIALOG FOR NAMING RULES ===== */
    .modal-backdrop {
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: rgba(0,0,0,0.5);
      z-index: 2000;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .modal {
      background: #fff;
      padding: 1rem 1.5rem;
      border-radius: 6px;
      max-width: 400px;
      width: 90%;
      box-shadow: 0 5px 10px rgba(0,0,0,0.2);
    }
    .modal h2 {
      margin-bottom: 0.5rem;
      font-size: 1.2rem;
    }
    .modal label {
      font-weight: 600;
      font-size: 0.9rem;
      margin-top: 1rem;
      display: block;
    }
    .modal input[type="text"] {
      margin-top: 0.25rem;
      margin-bottom: 0.5rem;
      width: 100%;
      box-sizing: border-box;
    }
    .modal-buttons {
      text-align: right;
      margin-top: 1rem;
    }
  </style>
</head>
<body>
<div class="container">

  <!-- Main Title -->
  <h1>Firewall Object Config Generator</h1>

  <!-- Control Bar with 6 columns -->
  <div class="control-bar">
    <!-- COLUMN 1: Vendor selection -->
    <div class="col">
      <div class="vendor-selector" id="vendorSelector">
        <div class="vendor-selection-button" id="vendorSelectionBtn" onclick="toggleVendorDropdown()">
          <img id="vendorLogo" src="https://companieslogo.com/img/orig/CSCO-187e9f61.png" alt="Vendor" />
          <span id="vendorLabel">Cisco ASA</span>
        </div>
        <div class="vendor-options" id="vendorOptions">
          <div class="vendor-option" onclick="selectVendor('cisco')">
            <img src="https://companieslogo.com/img/orig/CSCO-187e9f61.png" alt="Cisco ASA">
            <span>Cisco ASA</span>
          </div>
          <div class="vendor-option" onclick="selectVendor('paloalto')">
            <img src="https://companieslogo.com/img/orig/PANW-4618d203.png" alt="Palo Alto">
            <span>Palo Alto</span>
          </div>
          <div class="vendor-option" onclick="selectVendor('fortinet')">
            <img src="https://companieslogo.com/img/orig/FTNT-745f92ba.png" alt="Fortinet">
            <span>Fortinet</span>
          </div>
          <div class="vendor-option" onclick="selectVendor('checkpoint')">
            <img src="https://companieslogo.com/img/orig/CHKP-510367f9.png" alt="Check Point">
            <span>Check Point</span>
          </div>
          <!-- Juniper REMOVED -->
        </div>
      </div>
    </div><!-- end col1 -->

    <!-- COLUMN 2: Add Object & Reset -->
    <div class="col">
      <div class="button-group">
        <button class="button" onclick="addNewRow()">
          <i class="fa-solid fa-plus"></i> Add Object
        </button>
        <button class="button" onclick="resetTable()">
          <i class="fa-solid fa-arrows-rotate"></i> Reset
        </button>
      </div>
    </div><!-- end col2 -->

    <!-- COLUMN 3: Edit naming rules & Auto-naming -->
    <div class="col">
      <div class="button-group">
        <button class="button" onclick="openNamingRulesModal()">
          <i class="fa-solid fa-scroll"></i> Edit naming rules
        </button>
        <label>
          <input type="checkbox" id="autoNameCB" checked onclick="toggleAutoNaming()">
          Auto-naming
        </label>
      </div>
    </div><!-- end col3 -->

    <!-- COLUMN 4: Import CSV & Export CSV -->
    <div class="col">
      <div class="button-group">
        <button class="button" onclick="triggerCSVImport()">
          <i class="fa-solid fa-file-import"></i> Import CSV
        </button>
        <button class="button" onclick="exportToCSV()">
          <i class="fa-solid fa-file-export"></i> Export CSV
        </button>
      </div>
    </div><!-- end col4 -->

    <!-- COLUMN 5: Validate & Remove duplicates -->
    <div class="col">
      <div class="button-group">
        <button class="button" onclick="validateRows()">
          <i class="fa-solid fa-square-check"></i> Validate
        </button>
        <button class="button" id="removeDuplicatesBtn" style="display:none;" onclick="removeDuplicates()">
          <i class="fa-solid fa-filter-circle-xmark"></i> Remove duplicates
        </button>
      </div>
    </div><!-- end col5 -->

    <!-- COLUMN 6: Generate CLI -->
    <div class="col">
      <button class="button" onclick="generateCLI()">
        <i class="fa-solid fa-terminal"></i> Generate CLI
      </button>
    </div><!-- end col6 -->

  </div><!-- end .control-bar -->

  <!-- Error, Warning, and Success blocks -->
  <div id="errorBlock" class="error-block" style="display:none;"></div>
  <div id="warningBlock" class="warning-block" style="display:none;"></div>
  <div id="successBlock" class="success-block" style="display:none;"></div>

  <!-- Hidden file input for CSV import -->
  <input type="file" id="importCsvInput" accept=".csv" style="display:none;" />

  <!-- Table with NINE columns (Description, Comments, Color, and Tags all present) -->
  <table class="excel-table" id="mainTable">
    <thead>
      <tr>
        <th class="idx-col">
          #
          <div class="col-resize-handle"></div>
        </th>
        <th class="name-col">
          Object Name
          <div class="col-resize-handle"></div>
        </th>
        <th class="addr-col">
          Addresses
          <div class="col-resize-handle"></div>
        </th>
        <th id="descHeader" class="desc-col">
          Description
          <div class="col-resize-handle"></div>
        </th>
        <th id="commentsHeader" class="comments-col">
          Comments
          <div class="col-resize-handle"></div>
        </th>
        <th id="colorHeader" class="color-col">
          Color
          <div class="col-resize-handle"></div>
        </th>
        <th id="tagsHeader" class="tags-col">
          Tags
          <div class="col-resize-handle"></div>
        </th>
        <th class="groups-col">
          Groups
          <div class="col-resize-handle"></div>
        </th>
        <th class="actions-col">
          Actions
          <!-- no resize handle for Actions column -->
        </th>
      </tr>
    </thead>
    <tbody id="objectsTable"></tbody>
  </table>

  <!-- CLI output container -->
  <h2>CLI Commands:</h2>
  <div class="cli-output-container">
    <button class="copy-button" onclick="copyCLI()">Copy to clipboard</button>
    <div id="cliOutput" class="cli-output"></div>
  </div>
</div><!-- end .container -->

<!-- Modal for Naming Rules -->
<div id="namingRulesBackdrop" class="modal-backdrop" style="display:none;">
  <div class="modal">
    <h2>Edit Naming Rules</h2>
    <label>Host Prefix/Suffix</label>
    <input type="text" id="hostPrefix" placeholder="Default prefix for HOST_" />
    <input type="text" id="hostSuffix" placeholder="Default suffix (optional)" />

    <label>Network Prefix/Suffix</label>
    <input type="text" id="netPrefix" placeholder="Default prefix for NET_" />
    <input type="text" id="netSuffix" placeholder="Default suffix (e.g. m{CIDR})" />

    <label>FQDN Prefix/Suffix</label>
    <input type="text" id="fqdnPrefix" placeholder="Default prefix for FQDN_" />
    <input type="text" id="fqdnSuffix" placeholder="Default suffix (optional)" />

    <div class="modal-buttons">
      <button class="button" onclick="saveNamingRules()">Save</button>
      <button class="button delete-btn" onclick="closeNamingRulesModal()">Cancel</button>
    </div>
  </div>
</div>

<!-- Toast container -->
<div id="toastContainer"></div>

<script>
/********************************************************************
 * GLOBALS & DEFAULTS
 ********************************************************************/
let currentVendor = 'cisco'; // default
let autoNameEnabled = true;

// For duplicates
let duplicatesFound = false;

// Updated default naming rules: network suffix includes m{CIDR}
let namingRules = {
  hostPrefix: 'HOST_',
  hostSuffix: '',
  netPrefix:  'NET_',
  netSuffix:  'm{CIDR}',   // <--- changed here
  fqdnPrefix: 'FQDN_',
  fqdnSuffix: ''
};

/********************************************************************
 * VENDOR CONFIG
 *
 * We’ll keep it simple: Each vendor listing indicates which columns
 * are visible, and what header labels they should have.
 *
 * Columns order:
 *   0: # (index)
 *   1: Object Name
 *   2: Addresses
 *   3: Description
 *   4: Comments
 *   5: Color
 *   6: Tags
 *   7: Groups
 *   8: Actions
 *
 ********************************************************************/
const vendorData = {
  cisco: {
    label: 'Cisco ASA',
    logo: 'https://companieslogo.com/img/orig/CSCO-187e9f61.png',
    colHeaders: {
      desc: 'Remarks',
      comments: false,
      color: false,
      tags: false
    }
  },
  paloalto: {
    label: 'Palo Alto',
    logo: 'https://companieslogo.com/img/orig/PANW-4618d203.png',
    colHeaders: {
      desc: 'Description',
      comments: false,
      color: false,
      tags: 'Tags'
    }
  },
  fortinet: {
    label: 'Fortinet',
    logo: 'https://companieslogo.com/img/orig/FTNT-745f92ba.png',
    colHeaders: {
      desc: false,
      comments: 'Comments',
      color: 'Color',
      tags: false
    }
  },
  checkpoint: {
    label: 'Check Point',
    logo: 'https://companieslogo.com/img/orig/CHKP-510367f9.png',
    colHeaders: {
      desc: false,
      comments: 'Comments',
      color: 'Color',
      tags: 'Tags'
    }
  }
  // Juniper REMOVED
};

/********************************************************************
 * VENDOR DROPDOWN
 ********************************************************************/
function toggleVendorDropdown() {
  const opts = document.getElementById('vendorOptions');
  opts.style.display = (opts.style.display === 'block') ? 'none' : 'block';
}
function selectVendor(vendorKey) {
  currentVendor = vendorKey;
  const vData = vendorData[vendorKey];

  document.getElementById('vendorLogo').src = vData.logo;
  document.getElementById('vendorLabel').textContent = vData.label;
  document.getElementById('vendorOptions').style.display = 'none';

  updateUIForVendor();
}
document.addEventListener('click', (e) => {
  const dropdown = document.getElementById('vendorSelector');
  if (!dropdown.contains(e.target)) {
    document.getElementById('vendorOptions').style.display = 'none';
  }
});

/********************************************************************
 * NAMING RULES MODAL
 ********************************************************************/
function openNamingRulesModal() {
  // Populate fields
  document.getElementById('hostPrefix').value = namingRules.hostPrefix;
  document.getElementById('hostSuffix').value = namingRules.hostSuffix;
  document.getElementById('netPrefix').value  = namingRules.netPrefix;
  document.getElementById('netSuffix').value  = namingRules.netSuffix;
  document.getElementById('fqdnPrefix').value = namingRules.fqdnPrefix;
  document.getElementById('fqdnSuffix').value = namingRules.fqdnSuffix;

  document.getElementById('namingRulesBackdrop').style.display = 'flex';
}
function closeNamingRulesModal() {
  document.getElementById('namingRulesBackdrop').style.display = 'none';
}
function saveNamingRules() {
  namingRules.hostPrefix = document.getElementById('hostPrefix').value || '';
  namingRules.hostSuffix = document.getElementById('hostSuffix').value || '';
  namingRules.netPrefix  = document.getElementById('netPrefix').value  || '';
  namingRules.netSuffix  = document.getElementById('netSuffix').value  || '';
  namingRules.fqdnPrefix = document.getElementById('fqdnPrefix').value || '';
  namingRules.fqdnSuffix = document.getElementById('fqdnSuffix').value || '';

  closeNamingRulesModal();
}

/********************************************************************
 * AUTO-NAMING CHECKBOX
 ********************************************************************/
function toggleAutoNaming() {
  autoNameEnabled = document.getElementById('autoNameCB').checked;
}

/********************************************************************
 * RESET TABLE (ALSO CLEAR CLI OUTPUT)
 ********************************************************************/
function resetTable() {
  const tableBody = document.getElementById('objectsTable');
  tableBody.innerHTML = '';
  addNewRow(); // leaves a single blank row

  // Clear CLI & messages
  document.getElementById('cliOutput').textContent = '';
  document.getElementById('errorBlock').style.display = 'none';
  document.getElementById('warningBlock').style.display = 'none';
  document.getElementById('successBlock').style.display = 'none';

  // Hide remove duplicates button
  document.getElementById('removeDuplicatesBtn').style.display = 'none';
  duplicatesFound = false;
}

/********************************************************************
 * TABLE CREATION
 ********************************************************************/
function generateDefaultName(addr) {
  addr = addr.trim();
  if (!addr) return '';
  // Quick detection
  if (addr.includes('/')) {
    // treat it as a network
    // We'll do a simple text replacement of the /bits with m{bits} if suffix includes {CIDR}
    let cidr = addr.split('/')[1];
    let suffix = namingRules.netSuffix.replace('{CIDR}', cidr || '');
    return namingRules.netPrefix + addr.replace(/\//g, '_').replace(/[^a-zA-Z0-9._-]/g, '_') + suffix;
  } else if (/^\d+\.\d+\.\d+\.\d+$/.test(addr)) {
    // treat it as a host
    const clean = addr.replace(/[^0-9.]/g, '_');
    return namingRules.hostPrefix + clean + namingRules.hostSuffix;
  } else {
    // treat it as FQDN
    const clean = addr.replace(/[^a-zA-Z0-9._-]/g, '_');
    return namingRules.fqdnPrefix + clean + namingRules.fqdnSuffix;
  }
}
function isDefaultLike(str) {
  // a quick way to detect if user hasn't customized name
  if (!str) return true;
  // If it starts with one of our known prefixes
  if (
    str.startsWith(namingRules.hostPrefix) ||
    str.startsWith(namingRules.netPrefix)  ||
    str.startsWith(namingRules.fqdnPrefix)
  ) {
    return true;
  }
  return false;
}
function reindexRows() {
  const rows = document.querySelectorAll('#objectsTable tr');
  rows.forEach((row, idx) => {
    const firstCell = row.querySelector('td');
    if (firstCell) {
      firstCell.textContent = (idx + 1).toString();
    }
  });
}
function deleteRow(btn) {
  const row = btn.closest('tr');
  row.parentNode.removeChild(row);
  reindexRows();
}

function addNewRow(
  addressVal  = '',
  nameVal     = '',
  descVal     = '',
  commentsVal = '',
  colorVal    = '',
  tagsVal     = '',
  groupsVal   = ''
) {
  const table = document.getElementById('objectsTable');

  // Auto-name
  let finalName = nameVal;
  if (!finalName && addressVal && autoNameEnabled) {
    // If user didn’t specify a name, generate one
    finalName = generateDefaultName(addressVal.split(/[,\n]/)[0]);
  }

  const newRow = document.createElement('tr');
  newRow.innerHTML = `
    <td></td>
    <td><input type="text" value="${finalName}" /></td>
    <td><input type="text" value="${addressVal}" /></td>
    <td><input type="text" value="${descVal}" /></td>
    <td><input type="text" value="${commentsVal}" /></td>
    <td><input type="text" value="${colorVal}" /></td>
    <td><input type="text" value="${tagsVal}" /></td>
    <td><input type="text" value="${groupsVal}" /></td>
    <td style="text-align:center;">
      <button class="button delete-btn" onclick="deleteRow(this)">✕</button>
    </td>
  `;
  table.appendChild(newRow);
  reindexRows();

  // Add drag handles
  newRow.querySelectorAll('td').forEach((td, index) => {
    // skip # & actions
    if (index !== 0 && index !== 8) {
      const handle = document.createElement('div');
      handle.classList.add('drag-handle');
      handle.title = "Hold and drag to fill.";
      td.appendChild(handle);
    }
  });

  // If user changes the address while auto-naming is on, update name
  const addrInput = newRow.querySelector('td:nth-child(3) input');
  const nameInput = newRow.querySelector('td:nth-child(2) input');
  addrInput.addEventListener('input', () => {
    if (autoNameEnabled && isDefaultLike(nameInput.value)) {
      const firstAddr = addrInput.value.split(/[,\n]/)[0];
      nameInput.value = generateDefaultName(firstAddr);
    }
  });

  // Multi-paste
  addrInput.addEventListener('paste', e => {
    e.preventDefault();
    const pastedText = (e.clipboardData || window.clipboardData).getData('text');
    const addresses = pastedText.split(/[,\n]/).map(a => a.trim()).filter(Boolean);
    if (addresses.length === 0) return;

    // Fill the first row
    addrInput.value = addresses[0];
    if (autoNameEnabled && isDefaultLike(nameInput.value)) {
      nameInput.value = generateDefaultName(addresses[0]);
    }

    // Then for the rest
    const descV   = newRow.querySelector('td:nth-child(4) input').value;
    const commV   = newRow.querySelector('td:nth-child(5) input').value;
    const colV    = newRow.querySelector('td:nth-child(6) input').value;
    const tagsV   = newRow.querySelector('td:nth-child(7) input').value;
    const grpV    = newRow.querySelector('td:nth-child(8) input').value;

    for (let i = 1; i < addresses.length; i++) {
      addNewRow(addresses[i], '', descV, commV, colV, tagsV, grpV);
    }
  });

  updateUIForVendorRow(newRow);
}

/********************************************************************
 * DRAG FILL
 ********************************************************************/
let isDragging = false;
let dragStartRow = null;
let dragColumnIndex = null;
let sourceValue = '';
let originalUserSelect = '';

document.addEventListener('mousedown', (e) => {
  if (e.target.classList.contains('drag-handle')) {
    isDragging = true;
    const td = e.target.closest('td');
    dragColumnIndex = td.cellIndex;
    dragStartRow = td.parentNode.sectionRowIndex;
    const input = td.querySelector('input');
    sourceValue = input ? input.value : '';
    originalUserSelect = document.body.style.userSelect || '';
    document.body.style.userSelect = 'none';
  }
});
document.addEventListener('mouseup', () => {
  if (!isDragging) return;
  isDragging = false;
  removeDragHighlight();
  document.body.style.userSelect = originalUserSelect;
  dragStartRow = null;
  dragColumnIndex = null;
  sourceValue = '';
});
document.addEventListener('mousemove', (e) => {
  if (!isDragging) return;
  const table = document.getElementById('objectsTable');
  const rows = table.rows;
  removeDragHighlight();
  const td = e.target.closest('td');
  if (td && td.parentNode && td.parentNode.sectionRowIndex != null) {
    const endRow = td.parentNode.sectionRowIndex;
    if (endRow >= dragStartRow) {
      for (let i = dragStartRow; i <= endRow; i++) {
        rows[i].cells[dragColumnIndex].classList.add('drag-highlight');
        const inp = rows[i].cells[dragColumnIndex].querySelector('input');
        if (inp) inp.value = sourceValue;
      }
    } else {
      for (let i = endRow; i <= dragStartRow; i++) {
        rows[i].cells[dragColumnIndex].classList.add('drag-highlight');
        const inp = rows[i].cells[dragColumnIndex].querySelector('input');
        if (inp) inp.value = sourceValue;
      }
    }
  }
});
function removeDragHighlight() {
  document.querySelectorAll('.drag-highlight').forEach(cell => {
    cell.classList.remove('drag-highlight');
  });
}

/********************************************************************
 * COLUMN RESIZING
 ********************************************************************/
let isResizingCol = false;
let startX, startWidth, currentTh;

document.addEventListener('mousedown', (e) => {
  if (!e.target.classList.contains('col-resize-handle')) return;
  isResizingCol = true;
  currentTh = e.target.parentNode;
  startX = e.clientX;
  startWidth = currentTh.offsetWidth;
  document.body.style.userSelect = 'none';
});
document.addEventListener('mousemove', (e) => {
  if (!isResizingCol) return;
  const dx = e.clientX - startX;
  let newWidth = startWidth + dx;
  if (newWidth < 50) newWidth = 50;
  currentTh.style.width = newWidth + 'px';
});
document.addEventListener('mouseup', () => {
  if (isResizingCol) {
    isResizingCol = false;
    document.body.style.userSelect = '';
  }
});

/********************************************************************
 * UPDATE UI FOR VENDOR
 ********************************************************************/
function updateUIForVendor() {
  const vData = vendorData[currentVendor] || vendorData.cisco;
  const { desc, comments, color, tags } = vData.colHeaders;

  // 1) Update table header text or hide columns
  const descTh     = document.getElementById('descHeader');
  const commentsTh = document.getElementById('commentsHeader');
  const colorTh    = document.getElementById('colorHeader');
  const tagsTh     = document.getElementById('tagsHeader');

  function setHeader(thElem, label) {
    if (label === false) {
      thElem.style.display = 'none';
    } else {
      thElem.style.display = '';
      thElem.textContent = label;
    }
  }

  setHeader(descTh,     desc);
  setHeader(commentsTh, comments);
  setHeader(colorTh,    color);
  setHeader(tagsTh,     tags);

  // 2) For each row, show/hide the appropriate cells
  const rows = document.querySelectorAll('#objectsTable tr');
  rows.forEach(row => updateUIForVendorRow(row));
}

function updateUIForVendorRow(tr) {
  const vData = vendorData[currentVendor] || vendorData.cisco;
  const { desc, comments, color, tags } = vData.colHeaders;

  // indexes: 3=desc, 4=comments, 5=color, 6=tags
  function setCellDisplay(td, configVal) {
    if (configVal === false) td.style.display = 'none';
    else td.style.display = '';
  }
  setCellDisplay(tr.cells[3], desc);
  setCellDisplay(tr.cells[4], comments);
  setCellDisplay(tr.cells[5], color);
  setCellDisplay(tr.cells[6], tags);
}

/********************************************************************
 * VALIDATION & DUPLICATES
 ********************************************************************/
function validateAddress(addr) {
  // IP or IP/CIDR
  const ipPattern = /^(\d{1,3}\.){3}\d{1,3}(?:\/\d{1,2})?$/;
  // FQDN
  const domainPattern = /^(?=.{1,253}$)(?!\d+$)(?!.*\.\d+$)(?!-)[a-zA-Z0-9-]{1,63}(?<!-)(\.[a-zA-Z0-9-]{1,63}(?<!-))+$/;
  if (ipPattern.test(addr)) {
    // quick octet check
    const [ipPart, cidr] = addr.split('/');
    const octets = ipPart.split('.');
    for (let o of octets) {
      const val = parseInt(o, 10);
      if (val < 0 || val > 255 || o === '') {
        return `Invalid IP octet "${o}" in "${addr}"`;
      }
    }
    if (cidr) {
      const bits = parseInt(cidr, 10);
      if (bits < 1 || bits > 32) {
        return `Invalid CIDR /${bits} in "${addr}"`;
      }
    }
    return null; // valid
  }
  else if (domainPattern.test(addr)) {
    return null; // valid FQDN
  }
  return `Not a valid IP/CIDR or FQDN: "${addr}"`;
}

function cidrToNetmask(bits) {
  const mask = [0,0,0,0];
  let b = parseInt(bits, 10);
  for (let i=0; i<4; i++) {
    const take = Math.min(b, 8);
    mask[i] = 256 - Math.pow(2, 8 - take);
    b -= take;
    if (b < 0) b=0;
  }
  return mask.join('.');
}

function runValidation() {
  const rows = document.querySelectorAll('#objectsTable tr');
  const errorBlock = document.getElementById('errorBlock');
  const warningBlock = document.getElementById('warningBlock');
  const successBlock = document.getElementById('successBlock');

  errorBlock.style.display = 'none';
  warningBlock.style.display = 'none';
  successBlock.style.display = 'none';
  errorBlock.innerHTML = '';
  warningBlock.innerHTML = '';
  successBlock.innerHTML = '';

  let errors = [];
  let warnings = [];
  let validObjects = [];
  let rowHasErrorMap = new Map();
  let rowHasWarningMap = new Map();

  // Track used names so we can detect collisions
  let usedNames = new Set();
  // Check for duplicates
  let addrRowMap = new Map();

  // First, gather addresses
  rows.forEach(row => {
    row.classList.remove('invalid-row','warning-row');
    const tds = row.querySelectorAll('td');
    if (tds.length < 9) return;
    const addrVal = tds[2].querySelector('input').value;
    const addresses = addrVal.split(/[,\n]/).map(a => a.trim()).filter(Boolean);
    addresses.forEach(a => {
      if (!addrRowMap.has(a)) addrRowMap.set(a, []);
      addrRowMap.get(a).push(row);
    });
  });

  // Then validate row by row
  rows.forEach(row => {
    const idxText = row.cells[0].textContent;
    const tds = row.querySelectorAll('td');
    if (tds.length < 9) return;

    const nameVal     = tds[1].querySelector('input').value.trim();
    const addrVal     = tds[2].querySelector('input').value.trim();
    const descVal     = tds[3].querySelector('input').value.trim();
    const commentsVal = tds[4].querySelector('input').value.trim();
    const colorVal    = tds[5].querySelector('input').value.trim();
    const tagsVal     = tds[6].querySelector('input').value.trim();
    const groupsVal   = tds[7].querySelector('input').value.trim();

    const addresses = addrVal.split(/[,\n]/).map(a => a.trim()).filter(Boolean);
    let rowErrored = false;

    // Check addresses
    if (addresses.length === 0) {
      errors.push(`Row ${idxText}: Missing addresses.`);
      rowErrored = true;
    }
    // Duplicate name check
    if (nameVal && usedNames.has(nameVal)) {
      errors.push(`Row ${idxText}: Object name "${nameVal}" is already used.`);
      rowErrored = true;
    }

    let finalName = nameVal;
    if (!finalName && addresses.length) {
      if (!autoNameEnabled) {
        errors.push(`Row ${idxText}: Missing object name.`);
        rowErrored = true;
      } else {
        finalName = generateDefaultName(addresses[0]);
      }
    }

    // Validate each address
    let rowObjs = [];
    addresses.forEach(a => {
      const valErr = validateAddress(a);
      if (valErr) {
        errors.push(`Row ${idxText}: ${valErr}`);
        rowErrored = true;
      } else {
        rowObjs.push({
          rowIdx: idxText,
          name: finalName,
          address: a,
          desc: descVal,
          comments: commentsVal,
          color: colorVal,
          tags: tagsVal.split(',').map(s => s.trim()).filter(Boolean),
          groups: groupsVal.split(',').map(s => s.trim()).filter(Boolean)
        });
      }
    });

    if (rowErrored) {
      rowHasErrorMap.set(row, true);
    } else {
      usedNames.add(finalName);
      validObjects.push(...rowObjs);
    }
  });

  // Duplicates => warnings
  duplicatesFound = false;
  addrRowMap.forEach((rowsForAddr, address) => {
    if (rowsForAddr.length > 1) {
      duplicatesFound = true;
      // Mark them as warnings if they're not already errors
      let rowIndices = [];
      rowsForAddr.forEach(r => {
        if (!rowHasErrorMap.has(r)) {
          rowHasWarningMap.set(r, true);
        }
        rowIndices.push(r.cells[0].textContent);
      });
      warnings.push(`Duplicate address "${address}" on rows [${rowIndices.join(', ')}].`);
    }
  });

  // Mark rows
  rows.forEach(r => {
    if (rowHasErrorMap.has(r)) {
      r.classList.add('invalid-row');
    } else if (rowHasWarningMap.has(r)) {
      r.classList.add('warning-row');
    }
  });

  return { validObjects, errors, warnings };
}

function validateRows() {
  const { errors, warnings } = runValidation();
  const errorBlock = document.getElementById('errorBlock');
  const warningBlock = document.getElementById('warningBlock');
  const successBlock = document.getElementById('successBlock');

  if (errors.length > 0) {
    errorBlock.style.display = 'block';
    errorBlock.innerHTML = '<strong>Some rows have errors:</strong><br><br>' +
      errors.map(e => '• ' + e).join('<br>');
  }
  if (warnings.length > 0) {
    warningBlock.style.display = 'block';
    warningBlock.innerHTML = '<strong>Some warnings:</strong><br><br>' +
      warnings.map(w => '• ' + w).join('<br>');
  }
  if (errors.length === 0 && warnings.length === 0) {
    successBlock.style.display = 'block';
    successBlock.innerHTML = '<strong>No errors or warnings!</strong>';
  }

  // If duplicates were found, show button
  if (duplicatesFound) {
    document.getElementById('removeDuplicatesBtn').style.display = 'inline-flex';
  } else {
    document.getElementById('removeDuplicatesBtn').style.display = 'none';
  }
}

/********************************************************************
 * REMOVE DUPLICATES
 ********************************************************************/
function removeDuplicates() {
  const { errors, warnings, validObjects } = runValidation();
  if (!duplicatesFound) return;

  let seenAddrs = new Set();
  const rows = [...document.querySelectorAll('#objectsTable tr')];
  for (let row of rows) {
    const addrVal = row.cells[2].querySelector('input').value;
    const addresses = addrVal.split(/[,\n]/).map(a => a.trim()).filter(Boolean);

    let doRemove = false;
    for (let a of addresses) {
      if (seenAddrs.has(a)) {
        doRemove = true;
        break;
      }
    }
    if (doRemove) {
      row.parentNode.removeChild(row);
    } else {
      addresses.forEach(a => seenAddrs.add(a));
    }
  }

  reindexRows();
  document.getElementById('removeDuplicatesBtn').style.display = 'none';
  duplicatesFound = false;
  showToast('Duplicates removed.');
}

/********************************************************************
 * GENERATE CLI
 ********************************************************************/
function generateCLI() {
  const { validObjects, errors, warnings } = runValidation();
  const cliDiv = document.getElementById('cliOutput');
  cliDiv.textContent = '';

  const errorBlock = document.getElementById('errorBlock');
  const warningBlock = document.getElementById('warningBlock');
  const successBlock = document.getElementById('successBlock');

  if (errors.length > 0) {
    errorBlock.style.display = 'block';
    errorBlock.innerHTML =
      '<strong>Some rows have errors (excluded from output):</strong><br><br>' +
      errors.map(e => '• ' + e).join('<br>');
  }
  if (warnings.length > 0) {
    warningBlock.style.display = 'block';
    warningBlock.innerHTML =
      '<strong>Warnings:</strong><br><br>' +
      warnings.map(w => '• ' + w).join('<br>');
  }
  if (errors.length === 0 && warnings.length === 0) {
    successBlock.style.display = 'block';
    successBlock.innerHTML = '<strong>No errors or warnings!</strong>';
  }

  if (validObjects.length === 0) {
    cliDiv.textContent = '(No valid objects.)';
    return;
  }

  // Build a group map
  let groupMap = new Map();
  validObjects.forEach(o => {
    o.groups.forEach(g => {
      if (!groupMap.has(g)) groupMap.set(g, []);
      groupMap.get(g).push(o.name);
    });
  });

  let lines = [];
  switch(currentVendor) {
    case 'cisco':
      lines.push('=== Cisco ASA Configuration ===');
      validObjects.forEach(o => {
        lines.push(`object network ${o.name}`);
        if (o.desc) lines.push(` remark ${o.desc}`);
        if (/^\d+\.\d+\.\d+\.\d+\/\d+$/.test(o.address)) {
          lines.push(` subnet ${o.address}`);
        } else if (/^\d+\.\d+\.\d+\.\d+$/.test(o.address)) {
          lines.push(` host ${o.address}`);
        } else {
          lines.push(` fqdn ${o.address}`);
        }
        lines.push('');
      });
      if (groupMap.size > 0) {
        lines.push('=== Cisco Object-Groups ===');
        groupMap.forEach((members, groupName) => {
          const uniq = [...new Set(members)];
          lines.push(`object-group network ${groupName}`);
          uniq.forEach(m => lines.push(` network-object object ${m}`));
          lines.push('!');
        });
      }
      break;

    case 'checkpoint':
      lines.push('=== Check Point Configuration ===');
      validObjects.forEach(o => {
        if (/^\d+\.\d+\.\d+\.\d+/.test(o.address)) {
          const ipOnly = o.address.replace(/\/\d+$/, '');
          lines.push(`add host name ${o.name} ip-address ${ipOnly}`);
          if (o.comments) {
            lines.push(`set host name ${o.name} comments "${o.comments}"`);
          }
          if (o.color) {
            lines.push(`set host name ${o.name} color "${o.color}"`);
          }
          if (o.desc) {
            lines.push(`set host name ${o.name} description "${o.desc}"`);
          }
        } else {
          lines.push(`add dns-host name ${o.name} ipv4-address ${o.address}`);
          if (o.comments) {
            lines.push(`set dns-host name ${o.name} comments "${o.comments}"`);
          }
          if (o.color) {
            lines.push(`set dns-host name ${o.name} color "${o.color}"`);
          }
          if (o.desc) {
            lines.push(`set dns-host name ${o.name} description "${o.desc}"`);
          }
        }
        lines.push('');
      });
      if (groupMap.size > 0) {
        lines.push('=== Check Point Groups ===');
        groupMap.forEach((members, groupName) => {
          const uniq = [...new Set(members)];
          lines.push(`add group name ${groupName} members ${uniq.join(' ')}`);
        });
      }
      break;

    case 'fortinet':
      lines.push('=== Fortinet Configuration ===');
      if (validObjects.length > 0) {
        lines.push('config firewall address');
        validObjects.forEach(o => {
          lines.push(`    edit "${o.name}"`);
          if (/^\d+\.\d+\.\d+\.\d+\/\d+$/.test(o.address)) {
            const [ipPart, bits] = o.address.split('/');
            const mask = cidrToNetmask(bits);
            lines.push(`        set type ipmask`);
            lines.push(`        set subnet ${ipPart} ${mask}`);
          } else if (/^\d+\.\d+\.\d+\.\d+$/.test(o.address)) {
            lines.push(`        set type ipmask`);
            lines.push(`        set subnet ${o.address} 255.255.255.255`);
          } else {
            lines.push(`        set type fqdn`);
            lines.push(`        set fqdn ${o.address}`);
          }
          if (o.comments) {
            lines.push(`        set comment "${o.comments}"`);
          }
          if (o.color) {
            lines.push(`        # color: ${o.color}`);
          }
          lines.push(`    next`);
        });
        lines.push('end');
      }
      if (groupMap.size > 0) {
        lines.push('');
        lines.push('config firewall addrgrp');
        groupMap.forEach((members, groupName) => {
          const uniq = [...new Set(members)];
          lines.push(`    edit "${groupName}"`);
          lines.push(`        set member "${uniq.join('" "')}"`);
          lines.push(`    next`);
        });
        lines.push('end');
      }
      break;

    case 'paloalto':
      lines.push('=== Palo Alto Configuration ===');
      validObjects.forEach(o => {
        if (/^\d+\.\d+\.\d+\.\d+\/\d+$/.test(o.address)) {
          lines.push(`set address "${o.name}" ip-netmask ${o.address}`);
        } else if (/^\d+\.\d+\.\d+\.\d+$/.test(o.address)) {
          lines.push(`set address "${o.name}" ip-netmask ${o.address}/32`);
        } else {
          lines.push(`set address "${o.name}" fqdn ${o.address}`);
        }
        if (o.desc) {
          lines.push(`set address "${o.name}" description "${o.desc}"`);
        }
        if (o.comments) {
          lines.push(`# comments: ${o.comments}`);
        }
        if (o.color) {
          lines.push(`# color: ${o.color}`);
        }
        if (o.tags && o.tags.length > 0) {
          o.tags.forEach(t => {
            lines.push(`set address "${o.name}" tag "${t}"`);
          });
        }
        lines.push('');
      });
      if (groupMap.size > 0) {
        lines.push('=== Palo Alto Address-Groups ===');
        groupMap.forEach((members, groupName) => {
          const uniq = [...new Set(members)];
          const quotedMembers = uniq.map(m => `"${m}"`).join(' ');
          lines.push(`set address-group "${groupName}" static [ ${quotedMembers} ]`);
        });
      }
      break;

    default:
      lines.push('=== Generic Example ===');
      validObjects.forEach(o => {
        lines.push(`# ${o.name} => ${o.address} (desc=${o.desc}, comments=${o.comments}, color=${o.color}, tags=${o.tags.join(',')})`);
      });
      break;
  }

  cliDiv.textContent = lines.join('\n');
}

/********************************************************************
 * COPY & TOAST
 ********************************************************************/
function copyCLI() {
  const cliText = document.getElementById('cliOutput').textContent;
  navigator.clipboard.writeText(cliText).then(() => {
    showToast('Copied to clipboard!');
  }, () => {
    showToast('Unable to copy.');
  });
}
function showToast(msg) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 3000);
}

/********************************************************************
 * EXPORT & IMPORT CSV
 ********************************************************************/
function exportToCSV() {
  const rows = document.querySelectorAll('#objectsTable tr');
  let csvLines = [];
  csvLines.push([
    "Object Name","Addresses","Description","Comments","Color","Tags","Groups"
  ].join(','));

  rows.forEach(row => {
    const tds = row.querySelectorAll('td');
    if (tds.length < 9) return;
    const nameVal     = tds[1].querySelector('input').value;
    const addrVal     = tds[2].querySelector('input').value;
    const descVal     = tds[3].querySelector('input').value;
    const commentsVal = tds[4].querySelector('input').value;
    const colorVal    = tds[5].querySelector('input').value;
    const tagsVal     = tds[6].querySelector('input').value;
    const groupsVal   = tds[7].querySelector('input').value;

    const rowArr = [
      nameVal, addrVal, descVal, commentsVal, colorVal, tagsVal, groupsVal
    ].map(x => x.replace(/"/g, '""'));
    csvLines.push('"' + rowArr.join('","') + '"');
  });

  const csvContent = csvLines.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", "firewall_objects.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function triggerCSVImport() {
  document.getElementById('importCsvInput').value = '';
  document.getElementById('importCsvInput').click();
}

document.getElementById('importCsvInput').addEventListener('change', e => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = evt => {
    parseImportedCSV(evt.target.result);
  };
  reader.readAsText(file,'UTF-8');
});

function parseImportedCSV(csvText) {
  const lines = csvText.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  if (lines.length < 2) {
    showToast('No valid CSV lines found.');
    return;
  }
  // skip header
  lines.shift();

  resetTable();

  lines.forEach(line => {
    const cols = line.split(/,(?=(?:[^"]*"[^"]*")*[^"]*$)/).map(c => c.trim());
    const finalCols = cols.map(c => {
      let cc = c;
      if (cc.startsWith('"') && cc.endsWith('"')) {
        cc = cc.slice(1, -1);
      }
      return cc.replace(/""/g,'"');
    });
    const [n,a,d,cm,clr,tg,gp] = finalCols;
    addNewRow(a,n,d,cm,clr,tg,gp);
  });

  showToast('CSV imported successfully!');
}

/********************************************************************
 * ON PAGE LOAD
 ********************************************************************/
addNewRow();
updateUIForVendor();
</script>
</body>
</html>
