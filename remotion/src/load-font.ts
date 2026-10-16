import { loadFont as loadPoppinsFont } from "@remotion/google-fonts/Poppins";
import { loadFont as loadBebasNeueFont } from "@remotion/google-fonts/BebasNeue";
import { loadFont as loadFrauncesFont } from "@remotion/google-fonts/Fraunces";
import { loadFont as loadCaveatFont } from "@remotion/google-fonts/Caveat";

let fontsLoaded = false;
let fontFamilies = {
  sans: "sans-serif",
  condensed: "sans-serif",
  serif: "serif",
  handwriting: "cursive",
};

export const ensureFontsLoaded = () => {
  if (fontsLoaded) return fontFamilies;

  try {
    const poppins = loadPoppinsFont("normal", {
      weights: ["700", "800"],
      subsets: ["latin"],
      ignoreTooManyRequestsWarning: true,
    });
    const bebas = loadBebasNeueFont("normal", {
      weights: ["400"],
      subsets: ["latin"],
      ignoreTooManyRequestsWarning: true,
    });
    const fraunces = loadFrauncesFont("normal", {
      weights: ["400", "700"],
      subsets: ["latin"],
      ignoreTooManyRequestsWarning: true,
    });
    const caveat = loadCaveatFont("normal", {
      weights: ["400", "700"],
      subsets: ["latin"],
      ignoreTooManyRequestsWarning: true,
    });

    fontFamilies = {
      sans: poppins.fontFamily,
      condensed: bebas.fontFamily,
      serif: fraunces.fontFamily,
      handwriting: caveat.fontFamily,
    };
    fontsLoaded = true;
  } catch (err) {
    console.warn("Error loading Google Fonts via @remotion/google-fonts:", err);
  }

  return fontFamilies;
};

export const getFontFamilies = () => ensureFontsLoaded();
