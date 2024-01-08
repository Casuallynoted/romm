import cronstrue from "cronstrue";

export const views: Record<
  number,
  {
    view: string;
    icon: string;
    "size-xl": number;
    "size-lg": number;
    "size-md": number;
    "size-sm": number;
    "size-xs": number;
    "size-cols": number;
  }
> = {
  0: {
    view: "small",
    icon: "mdi-view-comfy",
    "size-xl": 1,
    "size-lg": 1,
    "size-md": 2,
    "size-sm": 2,
    "size-xs": 3,
    "size-cols": 4,
  },
  1: {
    view: "big",
    icon: "mdi-view-module",
    "size-xl": 2,
    "size-lg": 2,
    "size-md": 3,
    "size-sm": 3,
    "size-xs": 6,
    "size-cols": 6,
  },
  2: {
    view: "list",
    icon: "mdi-view-list",
    "size-xl": 12,
    "size-lg": 12,
    "size-md": 12,
    "size-sm": 12,
    "size-xs": 12,
    "size-cols": 12,
  },
};

export const defaultAvatarPath = "/assets/default_avatar.png";

export function toTop() {
  window.scrollTo({
    top: 0,
    left: 0,
    behavior: "smooth",
  });
}

export function normalizeString(s: string) {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

export function convertCronExperssion(expression: string) {
  let convertedExpression = cronstrue.toString(expression, { verbose: true });
  convertedExpression =
    convertedExpression.charAt(0).toLocaleLowerCase() +
    convertedExpression.substr(1);
  return convertedExpression;
}

export function regionToEmoji(region: string) {
  switch (region.toLowerCase()) {
    case "as":
    case "australia":
      return "🇦🇺";
    case "a":
    case "asia":
      return "🌏";
    case "b":
    case "bra":
    case "brazil":
      return "🇧🇷";
    case "c":
    case "canada":
      return "🇨🇦";
    case "ch":
    case "chn":
    case "china":
      return "🇨🇳";
    case "e":
    case "eu":
    case "europe":
      return "🇪🇺";
    case "f":
    case "france":
      return "🇫🇷";
    case "fn":
    case "finland":
      return "🇫🇮";
    case "g":
    case "germany":
      return "🇩🇪";
    case "gr":
    case "greece":
      return "🇬🇷";
    case "h":
    case "holland":
      return "🇳🇱";
    case "hk":
    case "hong kong":
      return "🇭🇰";
    case "i":
    case "italy":
      return "🇮🇹";
    case "j":
    case "jp":
    case "japan":
      return "🇯🇵";
    case "k":
    case "korea":
      return "🇰🇷";
    case "nl":
    case "netherlands":
      return "🇳🇱";
    case "no":
    case "norway":
      return "🇳🇴";
    case "pd":
    case "public domain":
      return "🇵🇱";
    case "r":
    case "russia":
      return "🇷🇺";
    case "s":
    case "spain":
      return "🇪🇸";
    case "sw":
    case "sweden":
      return "🇸🇪";
    case "t":
    case "taiwan":
      return "🇹🇼";
    case "u":
    case "us":
    case "usa":
      return "🇺🇸";
    case "uk":
    case "england":
      return "🇬🇧";
    case "unk":
    case "unknown":
      return "🌎";
    case "unl":
    case "unlicensed":
      return "🌎";
    case "w":
    case "global":
    case "world":
      return "🌎";
    default:
      return region;
  }
}

export function languageToEmoji(language: string) {
  switch (language.toLowerCase()) {
    case "ar":
    case "arabic":
      return "🇦🇪";
    case "da":
    case "danish":
      return "🇩🇰";
    case "de":
    case "german":
      return "🇩🇪";
    case "en":
    case "english":
      return "🇬🇧";
    case "es":
    case "spanish":
      return "🇪🇸";
    case "fi":
    case "finnish":
      return "🇫🇮";
    case "fr":
    case "french":
      return "🇫🇷";
    case "it":
    case "italian":
      return "🇮🇹";
    case "ja":
    case "japanese":
      return "🇯🇵";
    case "ko":
    case "korean":
      return "🇰🇷";
    case "nl":
    case "dutch":
      return "🇳🇱";
    case "no":
    case "norwegian":
      return "🇳🇴";
    case "pl":
    case "polish":
      return "🇵🇱";
    case "pt":
    case "portuguese":
      return "🇵🇹";
    case "ru":
    case "russian":
      return "🇷🇺";
    case "sv":
    case "swedish":
      return "🇸🇪";
    case "zh":
    case "chinese":
      return "🇨🇳";
    case "nolang":
    case "no language":
      return "🌎";
    default:
      return language;
  }
}
