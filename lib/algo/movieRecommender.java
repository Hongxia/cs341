import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

public class movieRecommender {

	static int k = 10;
	static double lambda = 0.12;
	static double lambda_beta = 0.5;
	static double eita = 0.01;
	static double eita_beta = 0.0001;
	static String filename = "./src/Books.csv";
	static String testFilename = "./src/Books.csv";
	static String lineSplit = ",";
	
	static Map<String, double[]> vectorps = new HashMap<String, double[]>();
	static Map<String, double[]> vectorqs = new HashMap<String, double[]>();
	static double objective = 0;
	
	static double alpha = 0;
	static int count = 0;
	static double betau = 0;
	static double betai = 0;
	
	public static void main(String[] args) throws NumberFormatException, IOException{
		
		getFileInfo();

		for (int i = 0; i < 40; i++){
			updateVectors();
		}
		
	}
	
	private static void updateVectors() throws NumberFormatException, IOException{
		BufferedReader br = new BufferedReader(new FileReader(filename));
		String line;
		while ((line = br.readLine()) != null){
			String[] lineparts = line.split(lineSplit);
			if (lineparts.length >= 3){
				String userid = lineparts[0];
				String movieid = lineparts[1];
				double rating = Double.parseDouble(lineparts[2]);
				double[] vectorp = vectorps.get(userid);
				double[] vectorq = vectorqs.get(movieid);
				
				double epsilon = rating;
				for (int i = 0; i < k; i++){
					epsilon -= vectorp[i]*vectorq[i];
				}
				epsilon -= alpha;
				epsilon -= betau;
				epsilon -= betai;
				
				double[] newvectorp = new double[k];
				for (int i = 0; i < k; i++){
					newvectorp[i] = vectorp[i] + eita*(epsilon*vectorq[i] - lambda*vectorp[i]);
				}

				double[] newvectorq = new double[k];
				for (int i = 0; i < k; i++){
					newvectorq[i] = vectorq[i] + eita*(epsilon*vectorp[i] - lambda*vectorq[i]);
				}
				
				
				vectorps.put(userid, newvectorp);
				vectorqs.put(movieid, newvectorq);

				betau = betau + eita_beta*(epsilon - lambda_beta*betau);
				betai = betai + eita_beta*(epsilon - lambda_beta*betai);
			}
		}
		br.close();
		System.out.println(objectiveFunc(vectorps, vectorqs));
		System.out.println("Test: " + testFunc(vectorps, vectorqs));
	}
	
	private static double testFunc(Map<String, double[]> vectorps, Map<String, double[]> vectorqs) throws NumberFormatException, IOException{
		BufferedReader br = new BufferedReader(new FileReader(testFilename));
		String line;
		double error = 0;
		while ((line = br.readLine()) != null){
			String[] lineparts = line.split(lineSplit);
			if (lineparts.length >= 3){
				String userid = lineparts[0];
				String movieid = lineparts[1];
				double rating = Double.parseDouble(lineparts[2]);
				if(vectorps.containsKey(userid) && vectorqs.containsKey(movieid)){
					double[] vectorp = vectorps.get(userid);
					double[] vectorq = vectorqs.get(movieid);
					
					double epsilon = rating;
					for (int i = 0; i < k; i++){
						epsilon -= vectorp[i]*vectorq[i];
					}
					epsilon -= alpha;
					epsilon -= betau;
					epsilon -= betai;
					error += epsilon*epsilon;
				}
			}
		}
		br.close();
		return error;
	}
	
	private static double objectiveFunc(Map<String, double[]> vectorps, Map<String, double[]> vectorqs) throws NumberFormatException, IOException{
		BufferedReader br = new BufferedReader(new FileReader(filename));
		String line;
		double error = 0;
		while ((line = br.readLine()) != null){
			String[] lineparts = line.split(lineSplit);
			if (lineparts.length >= 3){
				String userid = lineparts[0];
				String movieid = lineparts[1];
				double rating = Double.parseDouble(lineparts[2]);
				double[] vectorp = vectorps.get(userid);
				double[] vectorq = vectorqs.get(movieid);
				
				double epsilon = rating;
				for (int i = 0; i < k; i++){
					epsilon -= vectorp[i]*vectorq[i];
				}
				epsilon -= alpha;
				epsilon -= betau;
				epsilon -= betai;				
				error += epsilon*epsilon;
			}
		}
		@SuppressWarnings("rawtypes")
		Iterator itp = vectorps.entrySet().iterator();
		while (itp.hasNext()){
			@SuppressWarnings("unchecked")
			Map.Entry<Integer, double[]> pair = (Map.Entry<Integer, double[]>)itp.next();
			double[] vp = pair.getValue();
			for(int i = 0; i < k; i++){
				error += lambda*vp[i]*vp[i];
			}
		}
		@SuppressWarnings("rawtypes")
		Iterator itq = vectorqs.entrySet().iterator();
		while (itq.hasNext()){
			@SuppressWarnings("unchecked")
			Map.Entry<Integer, double[]> pair = (Map.Entry<Integer, double[]>)itq.next();
			double[] vq = pair.getValue();
			for(int i = 0; i < k; i++){
				error += lambda*vq[i]*vq[i];
			}
		}
		error += lambda_beta*betau*betau;
		error += lambda_beta*betai*betai;
		br.close();
		return error;
	}

	
	private static void getFileInfo() throws NumberFormatException, IOException {
		BufferedReader br = new BufferedReader(new FileReader(filename));
		String line;
		double sum = 0;
		while ((line = br.readLine()) != null){
			String[] lineparts = line.split(lineSplit);
			if (lineparts.length > 0){
				count++;
				sum += Double.parseDouble(lineparts[2]);
				String userid = lineparts[0];
				String movieid = lineparts[1];
				if (vectorps.containsKey(userid) == false){
					double[] vectorp = new double[k];
					for (int i = 0; i < k; i++){
						vectorp[i] = Math.random()/2;
					}
					vectorps.put(userid, vectorp);
				}
				if (vectorqs.containsKey(movieid) == false){
					double[] vectorq = new double[k];
					for (int i = 0; i < k; i++){
						vectorq[i] = Math.random()/2;
					}
					vectorqs.put(movieid, vectorq);
				}
			}
		}
		
		alpha = sum / count;
		br.close();
	}
}


