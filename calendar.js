/* Stockholm Guide: thin editorial adapter for FullCalendar Standard (MIT).
 * The calendar engine provides month/date/list navigation; our only custom work
 * is the verified editorial tags, filters, source links and flexible-date list.
 */
(() => {
  "use strict";
  const source = document.getElementById("calendar-data");
  if (!source) return;
  const guide = JSON.parse(source.textContent);
  const events = guide.events;
  const $ = id => document.getElementById(id);
  const today = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Europe/Stockholm", year: "numeric", month: "2-digit", day: "2-digit"
  }).format(new Date());
  let selected = events.map(e => e.date).filter(date => date && date >= today).sort()[0]
    || events.map(e => e.date).filter(Boolean).sort()[0]
    || guide.window_start;
  let category = "all";
  let search = "";

  const text = (tag, className, value) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (value != null) el.textContent = String(value);
    return el;
  };
  const formatDate = date => new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC", weekday: "long", day: "numeric", month: "long", year: "numeric"
  }).format(new Date(date + "T12:00:00Z"));
  const filtered = () => events.filter(e =>
    (category === "all" || (category === "last_chance" ? e.last_chance : e.section === category))
    && [e.title, e.venue, e.description, e.dates].join(" ").toLocaleLowerCase().includes(search)
  );

  function card(e) {
    const article = text("article", "event-card");
    const tags = text("div", "tags");
    if (e.section === "top3") tags.append(text("span", "tag featured", "TOP PICK"));
    if (e.section === "calendar_only_events") tags.append(text("span", "tag", "ALSO DISCOVERED"));
    if (e.last_chance) tags.append(text("span", "tag closing", "LAST CHANCE"));
    if (e.kind === "closing") tags.append(text("span", "tag", "CLOSING DAY"));
    if (e.kind === "flexible") tags.append(text("span", "tag", "FLEXIBLE DATE"));
    if (tags.childNodes.length) article.append(tags);
    article.append(text("h4", "", e.title));
    article.append(text("p", "when", e.dates || e.schedule_note || "Confirm organizer's dates"));
    if (e.venue) article.append(text("p", "where", e.venue));
    if (e.description) article.append(text("p", "description", e.description));
    if (e.price || e.booking) article.append(text("p", "booking",
      [e.price, e.booking].filter(Boolean).join(" · ")));
    const link = text("a", "", "View official event details");
    link.href = e.url;
    link.rel = "noopener noreferrer";
    link.target = "_blank";
    article.append(link);
    return article;
  }

  function display(container, rows, empty) {
    container.replaceChildren();
    if (!rows.length) container.append(text("p", "empty", empty));
    else for (const event of rows) container.append(card(event));
  }

  function renderSelected() {
    $("day-heading").textContent = formatDate(selected);
    const matches = filtered().filter(e => e.date === selected);
    $("day-count").textContent = matches.length + (matches.length === 1 ? " EVENT" : " EVENTS");
    display($("day-events"), matches, "No matching events on this date. Select another day or change the filters.");
  }
  function renderFlexible() {
    display($("flexible-events"), filtered().filter(e => e.kind !== "event"),
      "No flexible or last-chance experiences match these filters.");
  }

  function toCalendar(rows) {
    return rows.filter(e => e.date).map(e => ({
      id: e.id,
      title: e.kind === "closing" ? "Closes · " + e.title : e.title,
      start: e.date + (e.kind === "event" && e.time ? "T" + e.time + ":00" : ""),
      allDay: !(e.kind === "event" && e.time),
      extendedProps: {
        originalDate: e.date,
        section: e.section,
        last_chance: e.last_chance,
        original: e
      }
    }));
  }

  let calendar = null;
  if (window.FullCalendar && window.FullCalendar.Calendar) {
    calendar = new window.FullCalendar.Calendar($("fullcalendar"), {
      initialView: new URLSearchParams(location.search).get("view") === "agenda" ? "listMonth" : "dayGridMonth",
      initialDate: guide.window_start,
      firstDay: 1,
      timeZone: "Europe/Stockholm",
      height: "auto",
      fixedWeekCount: false,
      dayMaxEvents: 3,
      displayEventEnd: false,
      editable: false,
      selectable: false,
      eventOrder: "start,-duration,title",
      headerToolbar: { left: "prev,next today", center: "title", right: "" },
      buttonText: { today: "Today" },
      events: toCalendar(filtered()),
      dateClick: info => {
        selected = info.dateStr;
        renderSelected();
      },
      eventClick: info => {
        info.jsEvent.preventDefault();
        selected = info.event.extendedProps.originalDate;
        renderSelected();
        $("day-heading").scrollIntoView({ behavior: "smooth", block: "start" });
      },
      eventClassNames: info => [
        info.event.extendedProps.section === "top3" ? "fc-top-pick" : "",
        info.event.extendedProps.last_chance ? "fc-last-chance" : ""
      ].filter(Boolean),
      eventDidMount: info => {
        info.el.title = info.event.extendedProps.original.dates + " — " +
          info.event.extendedProps.original.venue;
      }
    });
    calendar.render();
  } else {
    // A blocked CDN must leave all useful dates and organizer links accessible.
    $("calendar-unavailable").hidden = false;
    display($("day-events"), filtered().filter(e => e.date),
      "No dated events available.");
    $("day-heading").textContent = "All dated events";
    $("day-count").textContent = "";
  }

  function refresh() {
    if (calendar) {
      calendar.removeAllEvents();
      calendar.addEventSource(toCalendar(filtered()));
      renderSelected();
    }
    renderFlexible();
    for (const button of document.querySelectorAll("[data-filter]")) {
      const active = category === button.dataset.filter;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    }
  }

  for (const button of document.querySelectorAll("[data-filter]")) {
    button.addEventListener("click", () => {
      category = button.dataset.filter;
      refresh();
    });
  }
  $("search").addEventListener("input", e => {
    search = e.target.value.trim().toLocaleLowerCase();
    refresh();
  });
  function refreshView() {
    const list = calendar && calendar.view.type === "listMonth";
    for (const button of document.querySelectorAll("[data-view]")) {
      const active = (button.dataset.view === "list") === !!list;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    }
  }
  for (const button of document.querySelectorAll("[data-view]")) {
    button.addEventListener("click", () => {
      if (calendar) calendar.changeView(button.dataset.view === "list" ? "listMonth" : "dayGridMonth");
      refreshView();
    });
  }
  refresh();
  refreshView();
})();
