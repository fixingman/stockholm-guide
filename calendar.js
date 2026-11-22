(() => {
  "use strict";
  const payload = document.getElementById("calendar-data");
  if (!payload) return;
  const data = JSON.parse(payload.textContent);
  const events = data.events;
  const $ = id => document.getElementById(id);
  const timeZone = "Europe/Stockholm";

  const today = new Intl.DateTimeFormat("sv-SE", {
    timeZone, year: "numeric", month: "2-digit", day: "2-digit"
  }).format(new Date());
  const eventDates = events.map(e => e.date).filter(Boolean).sort();
  const monthFloor = data.window_start.slice(0, 7);
  const monthCeiling = [data.window_end, ...eventDates].sort().at(-1).slice(0, 7);
  let month = monthFloor;
  let selectedDay = eventDates.find(date => date >= today) || eventDates[0] || data.window_start;
  let filter = "all";
  let query = "";
  let view = new URLSearchParams(location.search).get("view") === "agenda" ? "list" : "calendar";

  const dateObject = iso => new Date(iso + "T12:00:00Z");
  const prettyDate = iso => new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC", weekday: "long", day: "numeric", month: "long", year: "numeric"
  }).format(dateObject(iso));
  const prettyMonth = ym => new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC", month: "long", year: "numeric"
  }).format(dateObject(ym + "-01"));
  const dateKey = (y, m, d) =>
    String(y).padStart(4, "0") + "-" + String(m).padStart(2, "0") + "-" +
    String(d).padStart(2, "0");
  const matched = e => {
    const category = filter === "all" ||
      (filter === "last_chance" ? e.last_chance : e.section === filter);
    const haystack = [e.title, e.venue, e.description, e.dates].join(" ").toLocaleLowerCase();
    return category && haystack.includes(query);
  };
  const visible = () => events.filter(matched);

  function node(tag, className, value) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (value !== undefined && value !== null) el.textContent = String(value);
    return el;
  }

  function eventCard(event) {
    const card = node("article", "event-card");
    const tags = node("div", "tags");
    if (event.section === "top3") tags.append(node("span", "tag featured", "TOP PICK"));
    if (event.last_chance) tags.append(node("span", "tag closing", "LAST CHANCE"));
    if (event.kind === "flexible") tags.append(node("span", "tag", "FLEXIBLE DATES"));
    if (event.kind === "closing") tags.append(node("span", "tag", "CLOSING DAY"));
    if (tags.childNodes.length) card.append(tags);
    card.append(node("h4", "", event.title));
    card.append(node("p", "when", event.dates || event.schedule_note || "Check dates"));
    if (event.venue) card.append(node("p", "where", event.venue));
    if (event.description) card.append(node("p", "description", event.description));
    if (event.price || event.booking) {
      card.append(node("p", "booking", [event.price, event.booking].filter(Boolean).join(" · ")));
    }
    const link = node("a", "", "Official event details");
    link.href = event.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    card.append(link);
    return card;
  }

  function displayEvents(container, list, emptyText) {
    container.replaceChildren();
    if (!list.length) {
      container.append(node("p", "empty", emptyText));
    } else {
      for (const e of list) container.append(eventCard(e));
    }
  }

  function renderMonth() {
    $("month-heading").textContent = prettyMonth(month);
    $("prev-month").disabled = month <= monthFloor;
    $("next-month").disabled = month >= monthCeiling;
    const [year, mon] = month.split("-").map(Number);
    const offset = (new Date(Date.UTC(year, mon - 1, 1)).getUTCDay() + 6) % 7;
    const days = new Date(Date.UTC(year, mon, 0)).getUTCDate();
    const rows = Math.ceil((offset + days) / 7);
    const grid = $("month-grid");
    grid.replaceChildren();
    const matching = visible().filter(e => e.date);
    const buckets = new Map();
    for (const e of matching) {
      const values = buckets.get(e.date) || [];
      values.push(e);
      buckets.set(e.date, values);
    }

    for (let i = 0; i < rows * 7; i++) {
      const raw = new Date(Date.UTC(year, mon - 1, i - offset + 1));
      const d = dateKey(raw.getUTCFullYear(), raw.getUTCMonth() + 1, raw.getUTCDate());
      const sameMonth = raw.getUTCMonth() === mon - 1;
      const selected = d === selectedDay;
      const dayEvents = buckets.get(d) || [];
      const classes = [
        "calendar-day",
        !sameMonth ? "outside" : "",
        selected ? "selected" : "",
        d === today ? "today" : ""
      ].filter(Boolean).join(" ");
      const cell = node("button", classes);
      cell.type = "button";
      cell.setAttribute("aria-pressed", String(selected));
      cell.setAttribute("aria-label", prettyDate(d) + ", " +
        dayEvents.length + (dayEvents.length === 1 ? " event" : " events"));
      cell.append(node("span", "day-number", raw.getUTCDate()));
      if (dayEvents.length) {
        const snippets = node("span", "day-events");
        for (const e of dayEvents.slice(0, 2)) {
          snippets.append(node("span", "day-mini " +
            (e.last_chance ? "last" : e.section === "top3" ? "pick" : ""), e.title));
        }
        if (dayEvents.length > 2) snippets.append(node("span", "day-more", "+" + (dayEvents.length - 2) + " more"));
        cell.append(snippets);
        cell.append(node("span", "mobile-count", dayEvents.length));
      }
      cell.addEventListener("click", () => {
        selectedDay = d;
        if (month !== d.slice(0, 7)) month = d.slice(0, 7);
        renderMonth();
        renderSelectedDay();
      });
      grid.append(cell);
    }
  }

  function renderSelectedDay() {
    $("day-heading").textContent = prettyDate(selectedDay);
    const list = visible().filter(e => e.date === selectedDay);
    $("day-count").textContent = list.length + (list.length === 1 ? " EVENT" : " EVENTS");
    displayEvents($("day-events"), list, "No events for this day with the current filters. Try another date or switch filters.");
  }

  function renderAgenda() {
    const list = visible().filter(e => e.date);
    $("list-count").textContent = list.length + " DATED ENTRIES";
    const container = $("all-events");
    container.replaceChildren();
    if (!list.length) {
      displayEvents(container, [], "No dated events match these filters.");
      return;
    }
    let last = "";
    for (const event of list) {
      if (event.date !== last) {
        const heading = node("h3", "agenda-day", prettyDate(event.date));
        heading.style.gridColumn = "1 / -1";
        container.append(heading);
        last = event.date;
      }
      container.append(eventCard(event));
    }
  }

  function renderFlexible() {
    const items = visible().filter(e => e.kind !== "event");
    displayEvents($("flexible-events"), items,
      "No ongoing or flexible-date experiences match these filters.");
  }

  function render() {
    renderMonth();
    renderSelectedDay();
    renderAgenda();
    renderFlexible();
    $("calendar-view").hidden = view !== "calendar";
    $("list-view").hidden = view !== "list";
    for (const button of document.querySelectorAll("[data-view]")) {
      const active = button.dataset.view === view;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    }
    for (const button of document.querySelectorAll("[data-filter]")) {
      const active = button.dataset.filter === filter;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    }
  }

  $("prev-month").addEventListener("click", () => {
    if (month <= monthFloor) return;
    const [y, m] = month.split("-").map(Number);
    const d = new Date(Date.UTC(y, m - 2, 1));
    month = dateKey(d.getUTCFullYear(), d.getUTCMonth() + 1, 1).slice(0, 7);
    render();
  });
  $("next-month").addEventListener("click", () => {
    if (month >= monthCeiling) return;
    const [y, m] = month.split("-").map(Number);
    const d = new Date(Date.UTC(y, m, 1));
    month = dateKey(d.getUTCFullYear(), d.getUTCMonth() + 1, 1).slice(0, 7);
    render();
  });
  $("search").addEventListener("input", e => {
    query = e.target.value.trim().toLocaleLowerCase();
    render();
  });
  for (const button of document.querySelectorAll("[data-filter]")) {
    button.addEventListener("click", () => { filter = button.dataset.filter; render(); });
  }
  for (const button of document.querySelectorAll("[data-view]")) {
    button.addEventListener("click", () => {
      view = button.dataset.view;
      render();
    });
  }
  render();
})();
