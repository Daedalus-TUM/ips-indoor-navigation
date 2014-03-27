function Show_Stuff(Click_Menu)
// Function that will swap the display/no display for
// all content within span tags
{
  switch (Click_Menu)
  {
  case "hardware":
    hardware.style.display = "";
    software.style.display = "none";
    break;
  case "software":
    hardware.style.display = "none";
    software.style.display = "";
    break;
  case default:
    break;
  }
}
