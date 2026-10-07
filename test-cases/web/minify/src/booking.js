/**
 * Booking widget for the course page.
 *
 * Responsibilities:
 *  - fill the date dropdown with the available course dates
 *  - calculate the price summary whenever the number of participants changes
 *  - submit the booking to the backend
 *
 * NOTE: keep this file framework-free, it is embedded on partner sites too.
 */

// Price per participant in euro cents. Kept in cents to avoid rounding issues.
const PRICE_PER_PARTICIPANT_CENTS = 18900;

// Groups of 4 or more get a discount of 10 percent.
const GROUP_DISCOUNT_THRESHOLD = 4;
const GROUP_DISCOUNT_FACTOR = 0.9;

// The dates are rendered server-side into this list in production.
// For the static version we keep them here.
const AVAILABLE_DATES = [
  "2026-11-07",
  "2026-11-21",
  "2026-12-05",
  "2027-01-16",
];

/**
 * Formats an amount in cents as a localized euro string.
 * @param {number} cents - amount in euro cents
 * @returns {string} formatted amount, e.g. "189,00 €"
 */
function formatEuro(cents) {
  const formatter = new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" });
  return formatter.format(cents / 100);
}

/**
 * Calculates the total price for the given number of participants.
 * @param {number} participants - number of participants (1-8)
 * @returns {number} total price in cents
 */
function calculateTotalCents(participants) {
  let total = participants * PRICE_PER_PARTICIPANT_CENTS;
  if (participants >= GROUP_DISCOUNT_THRESHOLD) {
    // apply the group discount
    total = Math.round(total * GROUP_DISCOUNT_FACTOR);
  }
  return total;
}

/**
 * Fills the date dropdown.
 */
function renderDates() {
  const select = document.getElementById("course-date");
  for (const date of AVAILABLE_DATES) {
    const option = document.createElement("option");
    option.value = date;
    option.textContent = new Date(date).toLocaleDateString("de-DE");
    select.appendChild(option);
  }
}

/**
 * Updates the price summary below the form.
 */
function renderPrice() {
  const participantsInput = document.getElementById("participants");
  const participants = parseInt(participantsInput.value, 10) || 1;
  const total = calculateTotalCents(participants);
  const summary = document.getElementById("price-summary");
  summary.textContent = participants + " × " + formatEuro(PRICE_PER_PARTICIPANT_CENTS) + " = " + formatEuro(total);
  console.log("price updated", participants, total); // debug
}

/**
 * Sends the booking to the backend.
 * @param {SubmitEvent} event
 */
async function submitBooking(event) {
  event.preventDefault();
  const payload = {
    date: document.getElementById("course-date").value,
    participants: parseInt(document.getElementById("participants").value, 10),
  };
  console.log("submitting booking", payload); // debug
  const response = await fetch("/api/bookings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    alert("Booking failed, please try again.");
    return;
  }
  alert("Thank you! We sent you a confirmation email.");
}

// --- wire everything up -----------------------------------------------------
document.addEventListener("DOMContentLoaded", function () {
  renderDates();
  renderPrice();
  document.getElementById("participants").addEventListener("input", renderPrice);
  document.getElementById("booking-form").addEventListener("submit", submitBooking);
});
