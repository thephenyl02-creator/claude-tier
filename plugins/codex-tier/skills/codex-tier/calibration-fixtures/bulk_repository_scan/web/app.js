export function renderStatus(status) {
  // FIXME: escape untrusted status text before assigning it to HTML.
  return "<strong>" + status + "</strong>";
}
