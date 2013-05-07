/* 
* Multilateration zur Berechung von Positionen
*
* This program is free software; you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation; either version 2 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program; if not, write to the Free Software
* Foundation, 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*
*
* Autor: Markus Hefele
*
* Wer Numerik nicht kann, braucht gar nicht erst versuchen das hier zu verstehen.
* Wer es sich trotzdem antun will, kann mal in die multilat-doku.pdf schauen.
*
* um eine shared library zu erstellen folgende zwei Befehle ausfuehren
* gcc -c -fPIC -O3 multilat.c
* gcc -shared -o multilat.so multilat.o
*
*/


#include <stdio.h>
#include <math.h>

#define BASES 20	//Max Anz an Basen




//Anz der Basen
int n = 0;
//Koord der Basen
double base_x[BASES];
double base_y[BASES];
double base_z[BASES];
//Abstaende zu den Basen
double r[BASES];

double start_x = 10000;
double start_y = 10000;
double start_z = 10000;

double posx = 0;
double posy = 0;
double posz = 0;

//muss so sein
double erg[3];


double *grad_f(double x, double y, double z, int n);
double f(double x, double y, double z, int n);
double armijo(double x, double y, double z, int n);
int rechne(void);



double wrapper (double station[][3], double start[3], double radius[], int nn, double *refx, double *refy, double *refz) {
  int i=0;
  for (i=0;i<nn;i++) {
    base_x[i] = station[i][0];
    base_y[i] = station[i][1];
    base_z[i] = station[i][2];
    r[i] = radius[i];
  }
  n = nn;
  start_x = start[0];
  start_y = start[1];
  start_z = start[2];
  
  rechne();
  *refx = posx;
  *refy = posy;
  *refz = posz;
  double genauigkeit = 0.0;
  return genauigkeit;
}



int rechne() {

	double *richtung;
	double schritt = 0.0;
	double x = start_x;
	double y = start_y;
	double z = start_z;
	double x_neu = 0.0;
	double y_neu = 0.0;
	double z_neu = 0.0;
	int i = 0;
	
	

	while(i<300)
	{
		//Grad (google it!!)
		richtung = grad_f(x,y,z,n);
		//Schrittweite nach Armijo (google it!!)
		schritt = armijo(x,y,z,n);

		x_neu = x - schritt*richtung[0];
		y_neu = y - schritt*richtung[1];
		z_neu = z - schritt*richtung[2];
		i++;

		//auf Staionaritaet pruefen
		if (((x-x_neu)*(x-x_neu)+(y-y_neu)*(y-y_neu)+(z-z_neu)*(z-z_neu))<0.0001)
			break;
		x = x_neu;
		y = y_neu;
		z = z_neu;
		
	}

	x = x_neu;
	y = y_neu;
	z = z_neu;
    
	posx = x;
	posy = y;
	posz = z;

  	int ret = 0;
	return ret;
}

//zu minimierende Funktion f
double f(double x, double y, double z, int n) {

	int i = 0;
	double erg3 = 0.0;
	double zwi = 0.0;

	for(i = 0; i < n; i++)
	{
		zwi = (x-base_x[i])*(x-base_x[i])+(y-base_y[i])*(y-base_y[i])+(z-base_z[i])*(z-base_z[i])-r[i]*r[i];
		erg3 += zwi*zwi;
	}
	return erg3;

}

// grad(f)
double *grad_f(double x, double y, double z, int n) {

	
	erg[0] = 0.0; erg[1] = 0.0; erg[2] = 0.0;
	int i = 0;
	double zwi = 0.0;
	//x-Komp
	for (i = 0; i < n; i++)
	{
		zwi = (x-base_x[i])*(x-base_x[i])+(y-base_y[i])*(y-base_y[i])+(z-base_z[i])*(z-base_z[i])-r[i]*r[i];
		erg[0] += zwi * (x-base_x[i]);
		erg[1] += zwi * (y-base_y[i]); 
		erg[2] += zwi * (z-base_z[i]);
		
	}

	erg[0] = erg[0] *4;
	erg[1] = erg[1] *4;
	erg[2] = erg[2] *4;


	return erg;

}

//armijo-Schrittweite bestimmen
double armijo(double x, double y, double z, int n) {

	double schritt = 1;
	int i = 0;
	double ls = 0.0;
	double rs = 0.0;
	double *gradient;
	gradient = grad_f(x,y,z,n);

	while (i < 1200)
	{
		ls = f(x+schritt*(-gradient[0]),y+schritt*(-gradient[1]),z+schritt*(-gradient[2]),n);
		rs = f(x,y,z,n) + 0.5*schritt*(-gradient[0]*gradient[0]-gradient[1]*gradient[1]-gradient[2]*gradient[2]);
		if (ls <= rs)
			break;
		schritt = schritt / 2;
		i++;
	}

	return schritt;

}
