export function ThemeScript() {
  const code = `try{
    var t=localStorage.getItem("chuoai-theme");
    var dark=t?t==="dark":window.matchMedia("(prefers-color-scheme: dark)").matches;
    var root=document.documentElement;
    root.classList.toggle("dark",dark);
    root.style.colorScheme=dark?"dark":"light";
  }catch(e){}`;
  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}