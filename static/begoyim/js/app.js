/* BEGOYIM — kichik interaktivlik: menyu, sticky header, bog'liq hudud tanlovlari, PWA. */
(function ($) {
  "use strict";

  // Sticky header (EduWell custom.js dan soddalashtirilgan)
  $(window).on("scroll", function () {
    $("header").toggleClass("background-header", $(window).scrollTop() > 60);
  });

  // Mobil menyu
  $(".menu-trigger").on("click", function () {
    $(this).toggleClass("active");
    $(".header-area .nav").slideToggle(200);
  });
  $(".main-nav ul.nav .has-sub > a").on("click", function (e) {
    if (window.innerWidth < 768) {
      e.preventDefault();
      $(this).next(".sub-menu").slideToggle(150);
    }
  });

  // Viloyat -> tuman -> mahalla
  function reload($select, url, keepValue, emptyLabel) {
    return $.getJSON(url).then(function (data) {
      var current = keepValue ? $select.val() : "";
      $select.empty().append($("<option>").val("").text(emptyLabel || "---------"));
      data.results.forEach(function (item) {
        $select.append($("<option>").val(item.id).text(item.name));
      });
      if (current && $select.find('option[value="' + current + '"]').length) { $select.val(current); }
    });
  }
  $("select[data-region]").each(function () {
    var $region = $(this);
    var $district = $($region.data("region"));
    var $mahalla = $region.data("mahalla") ? $($region.data("mahalla")) : null;
    var dUrl = $region.data("districts-url"), mUrl = $region.data("mahallas-url");
    var dEmpty = $district.find("option[value='']").text();
    var mEmpty = $mahalla ? $mahalla.find("option[value='']").text() : "";
    function loadD(keep) { return $region.val() ? reload($district, dUrl + "?region=" + $region.val(), keep, dEmpty) : $.when($district.empty().append($("<option>").val("").text(dEmpty))); }
    function loadM(keep) { if (!$mahalla) return; return $district.val() ? reload($mahalla, mUrl + "?district=" + $district.val(), keep, mEmpty) : $mahalla.empty().append($("<option>").val("").text(mEmpty)); }
    $region.on("change", function () { loadD(false).then(function () { loadM(false); }); });
    $district.on("change", function () { loadM(false); });
    if (!$region.prop("disabled")) { loadD(true).then(function () { loadM(true); }); }
  });

  // Narx turi "Kelishiladi" bo'lsa narx maydonini o'chirish
  $("#id_price_type").on("change", function () {
    var neg = $(this).val() === "negotiable";
    $("#id_price").prop("disabled", neg).closest(".field").toggleClass("opacity-50", neg);
  }).trigger("change");

  // Tasdiqlash so'raladigan tugmalar
  $(document).on("submit", "form[data-confirm]", function (e) {
    if (!window.confirm($(this).data("confirm"))) { e.preventDefault(); }
  });

  // PWA service worker
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () { navigator.serviceWorker.register("/sw.js").catch(function () {}); });
  }
})(jQuery);
