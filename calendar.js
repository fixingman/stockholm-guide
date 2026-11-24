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

  // Browser-only personal calendar downloads. Never alters the read-only
  // subscription feed or publishes a multi-day busy calendar block.
  const icalEscape = value => String(value || "")
    .replace(/\\/g, "\\\\").replace(/\r\n?/g, "\n")
    .replace(/\n/g, "\\n").replace(/;/g, "\\;").replace(/,/g, "\\,");
  const encoder = new TextEncoder();
  function foldICal(line) {
    const output = [];
    let chunk = "", length = 0;
    for (const letter of line) {
      const bytes = encoder.encode(letter).length;
      if (length + bytes > 75) {
        output.push(chunk);
        chunk = " " + letter;
        length = 1 + bytes;
      } else {
        chunk += letter;
        length += bytes;
      }
    }
    output.push(chunk);
    return output.join("\r\n");
  }
  const asICalDay = date => date.replace(/-/g, "");
  const nextICalDay = date => {
    const [y, m, d] = date.split("-").map(Number);
    return new Date(Date.UTC(y, m - 1, d + 1)).toISOString().slice(0, 10).replace(/-/g, "");
  };
  function personalICal(e, choice) {
    const chosenDay = choice.date || "";
    const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
    const notes = [
      e.description || "",
      e.dates || "",
      choice.allDay
        ? "Personal visit reminder only. Check opening hours and booking with the organizer."
        : choice.endUtc ? "Check booking with the organizer." : "End time not confirmed; check organizer.",
      "Official event page: " + e.url
    ].filter(Boolean).join("\n");
    const lines = [
      "BEGIN:VCALENDAR", "VERSION:2.0",
      "PRODID:-//The Stockholm Guide//Personal event import//EN",
      "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
      "BEGIN:VEVENT",
      "UID:" + asICalDay(chosenDay) + "-" + e.id.replace(/[^a-zA-Z0-9-]/g, "") + "@fixingman.github.io",
      "DTSTAMP:" + stamp,
      "SUMMARY:" + icalEscape(e.title),
      "DESCRIPTION:" + icalEscape(notes),
      "LOCATION:" + icalEscape(e.venue)
    ];
    if (choice.allDay) {
      lines.push("DTSTART;VALUE=DATE:" + asICalDay(chosenDay));
      lines.push("DTEND;VALUE=DATE:" + nextICalDay(chosenDay));
      lines.push("TRANSP:TRANSPARENT", "STATUS:TENTATIVE");
    } else {
      lines.push("DTSTART:" + choice.startUtc);
      if (choice.endUtc) lines.push("DTEND:" + choice.endUtc);
    }
    lines.push("URL:" + e.url, "END:VEVENT", "END:VCALENDAR");
    return lines.map(foldICal).join("\r\n") + "\r\n";
  }
  function downloadPersonalICal(e, choice) {
    const blob = new Blob([personalICal(e, choice)], {type: "text/calendar;charset=utf-8"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "stockholm-guide-" + asICalDay(choice.date) + ".ics";
    document.body.append(link);
    link.click();
    link.remove();
    // Give browsers (especially mobile) enough time to initiate the download.
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }
  function visitPicker(e) {
    const details = text("details", "visit-picker");
    const summary = text("summary", "", "Choose a visit date");
    const label = text("label", "", "Your visit day");
    const input = document.createElement("input");
    input.type = "date";
    input.className = "visit-date";
    input.min = e.visit_window.start;
    input.max = e.visit_window.end;
    input.required = true;
    label.append(input);
    const button = text("button", "personal-download", "Add chosen day (.ics)");
    button.type = "button";
    const note = text("p", "visit-picker-note", "A free, all-day reminder on your chosen date—not an appointment or an all-week calendar block. Check opening hours first.");
    const message = text("p", "visit-picker-status");
    message.setAttribute("role", "status");
    button.addEventListener("click", () => {
      const date = input.value;
      if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || date < input.min || date > input.max) {
        message.textContent = "Choose a date within the published exhibition dates.";
        input.focus();
        return;
      }
      message.textContent = "";
      downloadPersonalICal(e, {date, allDay: true});
    });
    details.append(summary, label, button, note, message);
    return details;
  }
  function sessionPicker(e, selectedDate) {
    const details = text("details", "visit-picker");
    details.append(text("summary", "", "Choose a session"));
    const label = text("label", "", "Session");
    const select = document.createElement("select");
    select.className = "session-select";
    e.sessions.forEach((session, index) => {
      const option = text("option", "", session.label);
      option.value = String(index);
      select.append(option);
    });
    const preferred = e.sessions.findIndex(session => session.date === selectedDate);
    if (preferred >= 0) select.value = String(preferred);
    label.append(select);
    const add = text("button", "personal-download", "Add selected session (.ics)");
    add.type = "button";
    add.addEventListener("click", () => {
      const chosen = e.sessions[Number(select.value)];
      if (!chosen || !/^\d{8}T\d{6}Z$/.test(chosen.start_utc)) return;
      downloadPersonalICal(e, {
        date: chosen.date, startUtc: chosen.start_utc,
        endUtc: chosen.end_utc, allDay: false
      });
    });
    details.append(label, add);
    return details;
  }

  function card(e, selectedDate) {
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
    const actions = text("div", "event-actions");
    actions.append(link);
    if (e.ical_url && !(e.sessions && e.sessions.length > 1)) {
      const add = text("a", "event-ical-link", "Add to calendar (.ics)");
      add.href = e.ical_url;
      add.download = "stockholm-guide-" + e.ical_url.split("/").pop();
      add.setAttribute("aria-label", "Download calendar entry for " + e.title);
      actions.append(add);
    }
    article.append(actions);
    if (e.sessions && e.sessions.length > 1) article.append(sessionPicker(e, selectedDate));
    else if (e.visit_window) article.append(visitPicker(e));
    return article;
  }

  function display(container, rows, empty, selectedDate) {
    container.replaceChildren();
    if (!rows.length) container.append(text("p", "empty", empty));
    else for (const event of rows) container.append(card(event, selectedDate));
  }

  function renderSelected() {
    $("day-heading").textContent = formatDate(selected);
    const matches = filtered().filter(e => e.date === selected ||
      (e.sessions && e.sessions.some(session => session.date === selected)));
    $("day-count").textContent = matches.length + (matches.length === 1 ? " EVENT" : " EVENTS");
    display($("day-events"), matches, "No matching events on this date. Select another day or change the filters.", selected);
  }
  function renderFlexible() {
    display($("flexible-events"), filtered().filter(e => e.kind !== "event"),
      "No flexible or last-chance experiences match these filters.");
  }

  function toCalendar(rows) {
    return rows.flatMap(e => {
      if (!e.date) return [];
      const dates = (e.sessions && e.sessions.length > 1)
        ? e.sessions.map((session, index) => ({date: session.date, time: session.time, id: e.id + "-" + index}))
        : [{date: e.date, time: e.time, id: e.id}];
      return dates.map(item => ({
        id: item.id,
        title: e.kind === "closing" ? "Closes · " + e.title : e.title,
        start: item.date + (e.kind === "event" && item.time ? "T" + item.time + ":00" : ""),
        allDay: !(e.kind === "event" && item.time),
        extendedProps: {
          originalDate: item.date,
          section: e.section,
          last_chance: e.last_chance,
          original: e
        }
      }));
    });
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
  const copySubscription = $("copy-subscription-url");
  if (copySubscription) {
    copySubscription.addEventListener("click", async () => {
      const status = $("copy-subscription-feedback");
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error("Clipboard unavailable");
        await navigator.clipboard.writeText(guide.subscribe_url);
        status.textContent = "Feed URL copied. Paste it into your calendar app's subscription settings.";
      } catch (_) {
        // Avoid silent failure on browsers without Clipboard API permissions.
        status.textContent = "Copy this feed URL: " + guide.subscribe_url;
      }
    });
  }
  refresh();
  refreshView();
})();
